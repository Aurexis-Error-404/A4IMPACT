import { NextRequest, NextResponse } from "next/server";
import { getCommodityInsightByName } from "../../../../lib/canned-data";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(
  _request: NextRequest,
  { params }: { params: { commodity: string } },
) {
  const commodity = decodeURIComponent(params.commodity);
  try {
    const upstream = await fetch(
      `${BACKEND}/api/recommendation/${encodeURIComponent(commodity)}`,
      { method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store" },
    );
    if (!upstream.ok) throw new Error(`upstream ${upstream.status}`);
    const body = await upstream.json();
    return NextResponse.json(body);
  } catch {
    const insight = getCommodityInsightByName(commodity);
    if (!insight) return NextResponse.json({ error: "commodity_not_found" }, { status: 404 });
    return NextResponse.json(insight);
  }
}
