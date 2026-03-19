\# Benin Artifact Digital Exhibition



A machine-assisted digital reconstruction of Benin artifacts using:



\- Image pairing (main + detail)

\- CLIP embeddings for visual similarity

\- Automatic clustering

\- Historical catalog descriptions (Pitt Rivers, 1900)

\- Interactive HTML exhibition



\## Pipeline



1\. Pair artifact images

2\. Generate exhibition plates

3\. Compute CLIP embeddings

4\. Cluster artifacts

5\. Extract descriptions from PDF

6\. Merge metadata

7\. Build interactive exhibition



\## Run



```bash

python benin\_pipeline.py --images images --output benin\_output

python extract\_benin\_descriptions.py

python merge\_benin\_metadata.py

python build\_exhibition.py



Output



Clustered artifacts



Contact sheets



Enriched dataset



Interactive exhibition (HTML)



Research Context



Based on:

Antique Works of Art from Benin (Pitt Rivers, 1900)



Future Work



Semantic search



Object detection (motifs)



Timeline reconstruction



Interactive museum UI

