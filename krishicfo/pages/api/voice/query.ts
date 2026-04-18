import type { NextApiRequest, NextApiResponse } from "next";

// Stub — Member A wires the real pipeline here.
// Returns canned Cotton response for now so VoiceButton can be tested end-to-end.
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  return res.status(200).json({
    text_response_te:
      "Patti dhara ippudu MSP kanna ekkuvaga undi — hold cheyyandi. Rendu vaараalu vachi chudandi.",
    audio_base64: null,
    commodity_detected: "Cotton",
  });
}

export const config = {
  api: { bodyParser: false },
};
