import { http } from '@google-cloud/functions-framework';
import { ImageAnnotatorClient } from '@google-cloud/vision';
import { Storage } from '@google-cloud/storage';

// Initialize clients
const visionClient = new ImageAnnotatorClient();
const storage = new Storage();

// --- Configuration ---
const BUCKET_NAME = 'espclassifier'; // <-- CHANGE THIS
// ---------------------

http('classify', async (req, res) => {
  try {
    const base64Image = req.body?.image;
    const mimeType = req.body?.mimeType || 'image/jpeg'; // Assume JPEG if not specified

    if (!base64Image) {
      return res.status(400).send('Bad Request: Missing "image" field in request body.');
    }

    // Strip the prefix if it exists (e.g., 'data:image/jpeg;base64,')
    const prefixRegex = /^data:[a-z]+\/[a-z]+;base64,/;
    const cleanBase64 = base64Image.replace(prefixRegex, '');
    const imageBuffer = Buffer.from(cleanBase64, 'base64');

    // 2. Define File Path and Upload to GCS
    const fileName = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}.jpg`;
    const bucketFile = storage.bucket(BUCKET_NAME).file(fileName);

    await bucketFile.save(imageBuffer, {
      metadata: { contentType: mimeType }
    });

    const gcsUri = `gs://${BUCKET_NAME}/${fileName}`;
    
    // 3. Call Vision API using GCS URI
    const request = {
        image: {
            source: { imageUri: gcsUri },
        },
        features: [{ type: 'LABEL_DETECTION', maxResults: 5 }],
    };

    const [response] = await visionClient.annotateImage(request);
    
    const labels = response.labelAnnotations.map(l => ({
      description: l.description,
      score: l.score
    }));

    res.json({ labels });

  } catch (err) {
    console.error(`Error: ${err.message}`);
    res.status(500).send('Error processing image via GCS upload.');
  }
});