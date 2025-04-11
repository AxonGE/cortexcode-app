export default async function handler(req, res) {
  if (req.method === 'POST') {
    const body = req.body;

    console.log("📡 Relay received:", body);

    const forwardResponse = await fetch('https://hook.eu2.make.com/ucqur41zxfss6x9kmziwtuohwoysg96o', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const result = await forwardResponse.text();

    return res.status(200).json({
      ok: true,
      forwarded: true,
      make_response: result
    });
  } else {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }
}
