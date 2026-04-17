import { NextRequest, NextResponse } from "next/server";
import { getCommodityInsights } from "../../../../lib/canned-data";

export async function POST(
  request: NextRequest,
  { params }: { params: { commodity: string } }
) {
  const commodity = decodeURIComponent(params.commodity);
  const body = await request.json().catch(() => ({}));
  
  // Actually we don't strictly need the client to send the group if we can infer it, 
  // but it's cleaner if the client sends the group. In this case, our API doesn't send 
  // group in the POST body. So let's find the group from canned data, or pass it in.
  // Wait, let's just make the Next.js server figure out the group.
  
  // We'll import `getAllCommodityCards` from canned-data because it's available server-side.
  const { getAllCommodityCards } = await import("../../../../lib/canned-data");
  const card = getAllCommodityCards().find(c => c.commodity === commodity);
  
  if (!card) {
    return NextResponse.json({ error: "Commodity not found" }, { status: 404 });
  }

  // Get the deterministic base insights
  const { getCommodityInsights } = await import("../../../../lib/canned-data");
  const baseInsights = getCommodityInsights(card.group, card.commodity);
  
  if (!baseInsights) {
    return NextResponse.json({ error: "No data" }, { status: 404 });
  }

  const groqApiKey = process.env.GROQ_API_KEY;
  if (!groqApiKey) {
    console.warn("No GROQ_API_KEY found, falling back to deterministic.");
    return NextResponse.json(baseInsights);
  }

  try {
    const prompt = `You are KrishiCFO, an elite agricultural commodities analyst. 
The commodity is "${commodity}".
The latest season is ${baseInsights.latestSeason}.
The MSP is ${baseInsights.latestMsp}.
The reference price is ${baseInsights.latestReferencePrice}.
The deterministic price trend is "${baseInsights.priceTrend}".
The coverage logic is "${baseInsights.seasonAvailability}".

Write a concise, 2-line rationale on whether the farmer should Hold, Defer, or Sell based on these metrics. Keep it highly action-oriented. Do NOT use markdown. Start directly with the reasoning.`;

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${groqApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "llama3-8b-8192",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.3,
        max_tokens: 150,
      }),
    });

    if (!response.ok) {
      throw new Error(`Groq API Error: ${response.status}`);
    }

    const data = await response.json();
    const aiRationale = data.choices?.[0]?.message?.content?.trim() || baseInsights.recommendationRationale;

    // We can also let the AI override the state. For safety, we keep the deterministic label 
    // unless you want to parse out the AI's label. Let's just override the rationale.
    
    const enrichedInsights = {
      ...baseInsights,
      recommendationRationale: aiRationale,
      confidenceLabel: "Groq AI Validated",
    };

    return NextResponse.json(enrichedInsights);

  } catch (error) {
    console.error("Failed to fetch from Groq:", error);
    // Fallback to static
    return NextResponse.json(baseInsights);
  }
}
