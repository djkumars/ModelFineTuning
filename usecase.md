For learning Azure OpenAI model customization (fine-tuning) end-to-end, let's build a complete working solution:

Use Case: IT Service Desk Ticket Classifier
Input
Plain Text
Cannot login to Outlook after password reset
Expected Output
JSON
{
"Category": "Identity",
"Priority": "P1",
"AssignmentGroup": "IAM Team"
}

This is ideal because it demonstrates:

Fine-tuning
Structured output
Azure AI Foundry
Deployment
.NET API integration
Enterprise AI architecture
Solution Architecture
Plain Text
Historical Ticket Data
|
v
JSONL Dataset
|
v
Azure AI Foundry
Fine-Tuning Job
|
v
Custom GPT Model
|
v
Model Deployment
|
v
ASP.NET Core API
|
v
Consumer Application
Prerequisites
Azure Resources

Create:

1. Azure OpenAI Resource
Plain Text
Azure Portal
-> Create Resource
-> Azure OpenAI

Example:

Plain Text
Resource Name:
aoai-ticket-demo
 
Region:
East US
Sweden Central
France Central
2. Azure AI Foundry Project
Plain Text
Azure AI Foundry
-> Create Project

Example:

Plain Text
Project Name:
ticket-classifier-project
Step 1: Build Training Dataset

Create a file:

Plain Text
tickets-train.jsonl

Structure:

JSON
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Cannot login to Outlook"},{"role":"assistant","content":"{\"Category\":\"Identity\",\"Priority\":\"P1\",\"AssignmentGroup\":\"IAM Team\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"VPN disconnected after password change"},{"role":"assistant","content":"{\"Category\":\"Identity\",\"Priority\":\"P1\",\"AssignmentGroup\":\"IAM Team\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Laptop screen flickering"},{"role":"assistant","content":"{\"Category\":\"Hardware\",\"Priority\":\"P2\",\"AssignmentGroup\":\"Desktop Support\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Keyboard not working"},{"role":"assistant","content":"{\"Category\":\"Hardware\",\"Priority\":\"P3\",\"AssignmentGroup\":\"Desktop Support\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Unable to access payroll application"},{"role":"assistant","content":"{\"Category\":\"Application\",\"Priority\":\"P2\",\"AssignmentGroup\":\"Business Apps\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Payroll portal throws 500 error"},{"role":"assistant","content":"{\"Category\":\"Application\",\"Priority\":\"P2\",\"AssignmentGroup\":\"Business Apps\"}"}]}
Validation Dataset

Create:

Plain Text
tickets-validation.jsonl
JSON
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Outlook password not accepted"},{"role":"assistant","content":"{\"Category\":\"Identity\",\"Priority\":\"P1\",\"AssignmentGroup\":\"IAM Team\"}"}]}
{"messages":[{"role":"system","content":"Classify IT service desk tickets."},{"role":"user","content":"Monitor has display issue"},{"role":"assistant","content":"{\"Category\":\"Hardware\",\"Priority\":\"P2\",\"AssignmentGroup\":\"Desktop Support\"}"}]}
Minimum Dataset Recommendation

For learning:

Plain Text
50 examples

Good proof of concept:

Plain Text
200-500 examples

Enterprise quality:

Plain Text
1000-5000 examples
Step 2: Upload Dataset

Open:

Plain Text
Azure AI Foundry
 

Navigate:

Plain Text
Project
-> Fine-Tuning
-> Files

Upload:

Plain Text
tickets-train.jsonl
 
tickets-validation.jsonl
Step 3: Create Fine-Tuning Job

Navigate:

Plain Text
Models
-> Fine-Tuning
-> New Fine-Tuning Job

Select:

Plain Text
Base Model:
GPT-4o-mini

Attach:

Plain Text
Training:
tickets-train.jsonl
 
Validation:
tickets-validation.jsonl

Example:

Plain Text
Model Name:
ticket-classifier-v1

Click:

Plain Text
Train
Step 4: Monitor Training

Training states:

Plain Text
Queued
Running
Completed

You'll see:

Plain Text
Training Loss
Validation Loss

When completed Azure generates:

Plain Text
ft:gpt-4o-mini:ticket-classifier-v1
Step 5: Deploy Model

Open:

Plain Text
Models
-> Fine-Tuned Models

Select:

Plain Text
ticket-classifier-v1

Deploy:

Plain Text
Deployment Name:
ticket-classifier-prod
 

Example Endpoint:

Plain Text
https://aoai-ticket-demo.openai.azure.com
Step 6: Test from Foundry

Test prompt:

Plain Text
VPN stopped working after password reset

Expected:

JSON
{
"Category": "Identity",
"Priority": "P1",
"AssignmentGroup": "IAM Team"
}

Another:

Plain Text
Laptop overheating frequently

Expected:

JSON
{
"Category": "Hardware",
"Priority": "P2",
"AssignmentGroup": "Desktop Support"
}
Step 7: ASP.NET Core Web API

Create project

Shell
dotnet new webapi -n TicketClassifierApi
 
Install Packages
Shell
dotnet add package Azure.AI.OpenAI
dotnet add package Azure.Identity
appsettings.json
JSON
{
"AzureOpenAI": {
"Endpoint": "https://aoai-ticket-demo.openai.azure.com/",
"ApiKey": "YOUR_KEY",
"Deployment": "ticket-classifier-prod"
}
}
Request Model
C#
public class TicketRequest
{
public string Description { get; set; } = "";
}
Response Model
C#
public class TicketResponse
{
public string Category { get; set; } = "";
public string Priority { get; set; } = "";
public string AssignmentGroup { get; set; } = "";
}
Service
C#
using Azure;
using Azure.AI.OpenAI;
using OpenAI.Chat;
 
public class TicketClassificationService
{
private readonly ChatClient _chatClient;
 
public TicketClassificationService(
IConfiguration config)
{
var endpoint =
new Uri(config["AzureOpenAI:Endpoint"]);
 
var key =
config["AzureOpenAI:ApiKey"];
 
var deployment =
config["AzureOpenAI:Deployment"];
 
var client =
new AzureOpenAIClient(
endpoint,
new AzureKeyCredential(key));
 
_chatClient =
client.GetChatClient(deployment);
}
 
public async Task<string> ClassifyAsync(
string description)
{
var response =
await _chatClient.CompleteChatAsync(
description);
 
return response.Value.Content[0].Text;
}
}
Controller
C#
[ApiController]
[Route("api/tickets")]
public class TicketsController : ControllerBase
{
private readonly TicketClassificationService _service;
 
public TicketsController(
TicketClassificationService service)
{
_service = service;
}
 
[HttpPost("classify")]
public async Task<IActionResult> Classify(
TicketRequest request)
{
var result =
await _service.ClassifyAsync(
request.Description);
 
return Ok(result);
}
}
Dependency Injection

Program.cs

C#
builder.Services.AddSingleton<
TicketClassificationService>();
Test Request
HTTP
POST /api/tickets/classify

Body

JSON
{
"description":
"VPN disconnected after password reset"
}

Response

JSON
{
"Category": "Identity",
"Priority": "P1",
"AssignmentGroup": "IAM Team"
}
 
Production Version

A typical enterprise architecture would look like:

Plain Text
ASP.NET API
|
v
Fine-Tuned GPT Model
|
+----> Ticket Classification
|
+----> Priority Prediction
|
+----> Team Assignment
|
+----> Confidence Score

Then:

Plain Text
Classification
|
v
Azure Service Bus
|
v
ServiceNow / Jira / Remedy
Architect Interview Takeaway

If asked "Give a practical Azure OpenAI fine-tuning use case":

We fine-tuned GPT-4o-mini using historical ITSM tickets. The model learned ticket categorization, priority assignment, and routing rules. Training data was stored as JSONL, fine-tuned through Azure AI Foundry, deployed as a custom model endpoint, and consumed through an ASP.NET Core API. The solution reduced manual ticket triage effort and produced consistent structured JSON output for downstream ServiceNow automation.