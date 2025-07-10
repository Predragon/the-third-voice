export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed" });
  }

  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  const prompt = `Rewrite the following message in a ${tone.toLowerCase()} tone:\n\n${userInput}`;

  const hfResponse = await fetch("https://api-inference.huggingface.co/models/google/flan-t5-base", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.HF_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs: prompt }),
  });

  const result = await hfResponse.json();
  const output = result?.[0]?.generated_text || "No result";

  res.status(200).json({ rewritten: output });
      }
