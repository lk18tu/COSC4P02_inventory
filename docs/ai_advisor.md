# AI Inventory Advisor Documentation

This document provides detailed information about the AI Inventory Advisor feature within our Inventory Management System.

---

## Overview

The AI Inventory Advisor utilizes a Large Language Model (LLM) to deliver intelligent and timely inventory recommendations. This tool assists managers and inventory staff in decision-making regarding inventory management.

---

## How it Works

When a user submits a query, the system performs the following steps:

- **User Query Submission**: Frontend captures user input.
- **Backend API Call**: Backend sends a request to the LLM (DeepSeek R1).
- **AI Processing**: The AI analyzes the query using contextual inventory data.
- **Response Generation**: The AI returns a recommendation in natural language.
- **Result Display**: Frontend dynamically updates to display the AI recommendation.

---

## Integration Details

**Model**: DeepSeek Chat (DeepSeek R1)

**API Endpoint**: POST request to DeepSeek API's completion endpoint.

---

## Environment Variables Setup

API keys must be securely stored in the `.env` file at the project root.

---

## Usage Instructions

- Launch your Django development server.
- Navigate to the AI Advisor interface:
http://127.0.0.1:8000/Company_Name/inventory_analysis/advisor/

- Submit your inventory-related query.  
- Receive an AI-generated recommendation.

---

## Troubleshooting Common Issues

| Issue | Recommended Solution |
|-------|----------------------|
| API Authentication Error (401) | Verify `.env` has a valid API key |
| Slow response time | AI processing can take several seconds |
| Incorrect or Empty responses | Check your prompt and request formatting |
