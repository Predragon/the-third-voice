export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed" });
  }

  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  if (!userInput || userInput.trim().length < 5) {
    return res.status(400).json({ error: "Invalid message input" });
  }

  const prompt = `Rewrite the following message in a ${tone.toLowerCase()} tone:\n\n${userInput}`;

  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/google/flan-t5-base", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.HF_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    const result = await hfResponse.json();
    const output = result?.[0]?.generated_text;

    if (!output) {
      console.error("Hugging Face returned no output:", result);
      return res.status(502).json({ error: "Model failed to generate text" });
    }

    return res.status(200).json({ rewritten: output });

  } catch (error) {
    console.error("API error:", error);
    return res.status(500).json({ error: "Internal server error" });
  }
}
