## What Are API Parameters?

Parameters are inputs that API consumers provide when making requests. There are several types:

Type	Example	Description
Path Parameters	/vms/{id}	Part of the URL path
Query Parameters	/vms?limit=10&skip=0	After ? in the URL
Request Body	JSON payload	Data sent in POST/PUT requests
Headers	Authorization: Bearer token	Metadata in request headers


## What Are Rate Limits?
Rate limits are restrictions on how many API requests a client can make within a specific time window.

## Why Are Rate Limits Necessary?
Prevent Denial of Service (DoS): Without limits, a malicious actor (or buggy client) could flood your server with thousands of requests, crashing it or making it unresponsive for legitimate users.
Protect Server Resources: Each API call consumes CPU, memory, database connections. Unlimited requests can exhaust these resources.
Fair Usage: Ensures one user doesn't monopolize the API, allowing fair access for all consumers.
Cost Control: Cloud infrastructure often charges per request or compute time. Rate limits prevent unexpected bills.
API Stability: Prevents cascading failures when your backend services get overwhelmed.

## What Happens Without Rate Limits?

Server crashes under heavy load
Database connection pool exhaustion
Increased latency for all users
Vulnerability to brute-force attacks (e.g., password guessing)
Unpredictable infrastructure costs
Service degradation affecting legitimate users


## What Are Query Parameters?
Query parameters are optional key-value pairs appended to a URL after a ? symbol. They allow clients to customize API requests without changing the endpoint itself.
URL Structure:
```
https://api.example.com/vms?$page=0&$limit=50&$filter=name eq 'web-server'
                           └────────────────────────────────────────────┘
                                      Query Parameters
```            


## Why Are Query Parameters Necessary?
1. Pagination ($page, $limit)
Without pagination, if you have 100,000 VMs in your database:
Without: Returns ALL 100,000 records at once → slow, memory-intensive, crashes browser
With: Returns 50 records per page → fast, manageable chunks
2. Filtering ($filter)
Without: Client downloads all data and filters locally → wasteful
With: Server returns only matching records → efficient
3. Sorting (e.g., $orderby)
Without: Client must sort data after receiving it
With: Server returns pre-sorted data
4. Field Selection (e.g., $select)
Without: Returns all fields including large ones you don't need
With: Returns only requested fields → less bandwidth
