import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(
  _request: NextRequest,
  { params }: { params: { commodity: string } },
) {
  const commodity = decodeURIComponent(params.commodity);
  const upstream = await fetch(
    `${BACKEND}/api/recommendation/${encodeURIComponent(commodity)}`,
    { method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store" },
  );

  const body = await upstream.json();
  return NextResponse.json(body, { status: upstream.status });
}
