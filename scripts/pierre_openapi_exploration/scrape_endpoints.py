import urllib.request
import re
import json

base_url = 'https://docs.pierre.finance'

links = [
    '/api-reference/rest/get-api-key-info',
    '/api-reference/rest/get-accounts',
    '/api-reference/rest/get-balance',
    '/api-reference/rest/get-balance-by-account',
    '/api-reference/rest/get-transactions',
    '/api-reference/rest/get-installments',
    '/api-reference/rest/get-bills',
    '/api-reference/rest/get-bill-summary',
    '/api-reference/rest/manage-closing-date',
    '/api-reference/rest/create-spending-limit',
    '/api-reference/rest/list-spending-limits',
    '/api-reference/rest/get-spending-limit-transactions',
    '/api-reference/rest/update-spending-limit',
    '/api-reference/rest/delete-spending-limit',
    '/api-reference/rest/confirm-spending-limit',
    '/api-reference/rest/create-payment-reminder',
    '/api-reference/rest/list-payment-reminders',
    '/api-reference/rest/update-payment-reminder',
    '/api-reference/rest/delete-payment-reminder',
    '/api-reference/rest/get-expensive-categories',
    '/api-reference/rest/get-memories',
    '/api-reference/rest/get-open-finance-connection-flow',
    '/api-reference/rest/manual-update'
]

results = []

for link in links:
    try:
        req = urllib.request.Request(base_url + link, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Simple extraction using regex for Method and Path if they exist in Mintlify's typical metadata
        # Mintlify stores page data in <script id="__NEXT_DATA__" type="application/json">
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if match:
            data = json.loads(match.group(1))
            props = data.get('props', {}).get('pageProps', {})
            mdx = props.get('mdx', '')
            
            # The API definition is usually in pageProps.page.api
            page_meta = props.get('page', {})
            api_meta = page_meta.get('api', '')
            title = page_meta.get('title', '')
            description = page_meta.get('description', '')
            
            # Extract method and endpoint from api_meta (e.g., "GET /api/v1/accounts")
            method = "GET"
            endpoint = "/unknown"
            if api_meta:
                parts = api_meta.split(' ')
                if len(parts) >= 2:
                    method = parts[0]
                    endpoint = parts[1]
                    
            results.append({
                'link': link,
                'title': title,
                'method': method,
                'endpoint': endpoint,
                'description': description
            })
    except Exception as e:
        print(f"Error fetching {link}: {e}")

# Save to a JSON file for the LLM to read easily
with open('extracted_endpoints.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Successfully processed {len(results)} pages.")
