export default async function handler(req, res) {
  const userInput = req.body?.text;

  const prompt = `Rewrite the following message in a calm, emotionally constructive tone:\n\n${userInput}`;

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

  res.status(200).json({ result: output });
}
