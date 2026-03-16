##Created by Rice Lovers for the Amazon Nova Hackathon

# GreenRouting
GreenRouting is a semantic router that optimizes AI efficiency. It analyzes incoming prompts based on intent and size, then intelligently dispatches them to the most resource-efficient model available. By matching task complexity to model scale, GreenRouting ensures you never use more energy than a response truly requires.


## 🚀 Key Features
* **Carbon-Aware Routing:** Automatically switches between "Eco" (Lite) and "Power" (Pro) models based on live grid CO₂ data.
* **Semantic Caching:** Reuses previous high-similarity responses to achieve **0.00 mg** carbon impact for repeated queries.
* **Multimodal Support:** Integrated file attachment system (Images/PDFs) that triggers advanced reasoning agents.
* **ESG Reporting:** Generates downloadable PDF achievement certificates and CSV audit logs for corporate compliance.
* **Session Isolation:** Unique session tracking to ensure clean metrics for every user demo.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Custom CSS for minimalist/modern aesthetic)
* **Inference:** Amazon Bedrock (Nova, Claude 3.5, Llama 3.2, Mistral)
* **Database:** Amazon DynamoDB (Serverless logging and caching)
* **Cloud Backend:** AWS SDK for Python (Boto3)
* **Data APIs:** Real-time Electricity Maps / Carbon API integration

## 📥 Installation

1. **Clone the repository:**
   bash
   git clone [https://github.com/YOUR_USERNAME/GreenRouting.git](https://github.com/YOUR_USERNAME/GreenRouting.git)
   cd GreenRouting

2. **Install Dependencies**:
   pip install -r requirements.txt

3. **Environment setup**:
   Create a .env file in the root directory and add your credentials:
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   DYNAMODB_TABLE_NAME=Table name

4. **Launch the dashboard using Streamlit**:
   streamlit run app.py
