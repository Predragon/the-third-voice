export default async function handler(req, res) {
  const response = await fetch("https://api-inference.huggingface.co/models/google/flan-t5-base", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.HF_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ inputs: "Say hello in a friendly tone." }),
  });

  const data = await response.text(); // Not .json() to catch HTML errors
  res.status(200).send(data);
}
