export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Only POST method is allowed" });
  }

  const userInput = req.body?.message;
  const tone = req.body?.tone || "Kind";

  const prompt = `Rewrite the following message in a ${tone.toLowerCase()} tone:\n\n${userInput}`;

  try {
    const hfResponse = await fetch("https://api-inference.huggingface.co/models/mrm8488/t5-base-finetuned-common_gen", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.HF_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ inputs: prompt }),
    });

    const result = await hfResponse.json();

    // Check if result contains error
    if (result.error) {
      return res.status(500).json({ error: result.error });
    }

    const output = result?.[0]?.generated_text || "No result from model";
    res.status(200).json({ rewritten: output });

  } catch (err) {
    console.error("API call failed:", err);
    res.status(500).json({ error: "API call failed" });
  }
}
