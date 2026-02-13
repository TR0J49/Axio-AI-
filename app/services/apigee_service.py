"""
Apigee Service - Handles Apigee proxy bundle generation
"""
import io
import json
import zipfile
import requests
from flask import session

from app.config.settings import GPT_SERVER_URL, GPT_MODEL


def get_extraction_prompt():
    """Get the system prompt for extracting proxy details from natural language"""
    return """You are an Apigee proxy configuration extractor. Your job is to extract API proxy details from natural language descriptions.

Extract the following fields from the user's message:
- proxy_name: The name of the API proxy (lowercase, alphanumeric with hyphens)
- domain: The target backend domain (e.g., api.example.com)
- proxy_endpoint: The base path for the proxy endpoint (e.g., /v1, /api)
- target_endpoint: The base path on the target server (defaults to / if not specified)

IMPORTANT: You must respond ONLY with valid JSON. No explanations, no markdown, just pure JSON.

Example input: "Create a proxy named weather-api for api.weather.com with /forecast endpoint"
Example output:
{"proxy_name": "weather-api", "domain": "api.weather.com", "proxy_endpoint": "/forecast", "target_endpoint": "/"}

Example input: "Build an API proxy called user-service targeting users.mycompany.io/api/v2"
Example output:
{"proxy_name": "user-service", "domain": "users.mycompany.io", "proxy_endpoint": "/api/v2", "target_endpoint": "/api/v2"}

If any required field cannot be determined, set it to null.
Always respond with ONLY the JSON object, nothing else."""


def extract_proxy_details(message):
    """Extract proxy details from natural language using AI"""
    headers = {"Content-Type": "application/json"}

    conversation = [
        {"role": "system", "content": get_extraction_prompt()},
        {"role": "user", "content": message}
    ]

    payload = {
        "model": GPT_MODEL,
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": 512,
            "temperature": 0.1,
            "top_p": 0.9
        }
    }

    try:
        print(f"[Apigee] Extracting proxy details from: {message[:50]}...")
        response = requests.post(GPT_SERVER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"].strip()
            print(f"[Apigee] AI response: {content}")

            # Try to parse JSON from the response
            # Handle cases where AI might wrap in markdown code blocks
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block or (not line.startswith("```") and "{" in content):
                        json_lines.append(line)
                content = "\n".join(json_lines)

            # Find JSON object in the content
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                extracted = json.loads(json_str)
                print(f"[Apigee] Extracted details: {extracted}")
                return extracted, None

            return None, "Could not parse AI response as JSON"

    except json.JSONDecodeError as e:
        print(f"[Apigee] JSON parse error: {e}")
        return None, f"Failed to parse proxy details: {str(e)}"
    except requests.exceptions.RequestException as e:
        print(f"[Apigee] Request error: {e}")
        return None, f"AI service error: {str(e)}"
    except Exception as e:
        print(f"[Apigee] Unexpected error: {e}")
        return None, f"Unexpected error: {str(e)}"

    return None, "Failed to extract proxy details from the message"


def validate_proxy_details(details):
    """Validate that all required fields are present"""
    if not details:
        return False, "No proxy details provided"

    required_fields = ['proxy_name', 'domain']
    missing = []

    for field in required_fields:
        if not details.get(field):
            missing.append(field)

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Set defaults for optional fields
    if not details.get('proxy_endpoint'):
        details['proxy_endpoint'] = '/'
    if not details.get('target_endpoint'):
        details['target_endpoint'] = '/'

    # Ensure paths start with /
    if not details['proxy_endpoint'].startswith('/'):
        details['proxy_endpoint'] = '/' + details['proxy_endpoint']
    if not details['target_endpoint'].startswith('/'):
        details['target_endpoint'] = '/' + details['target_endpoint']

    # Sanitize proxy name (lowercase, alphanumeric with hyphens)
    proxy_name = details['proxy_name'].lower()
    proxy_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in proxy_name)
    proxy_name = '-'.join(filter(None, proxy_name.split('-')))  # Remove consecutive hyphens
    details['proxy_name'] = proxy_name

    return True, None


def generate_main_proxy_xml(proxy_name, description=None):
    """Generate the main apiproxy/[proxy_name].xml file"""
    desc = description or f"API Proxy for {proxy_name}"

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="{proxy_name}">
    <DisplayName>{proxy_name}</DisplayName>
    <Description>{desc}</Description>
    <CreatedAt>{{}}</CreatedAt>
    <LastModifiedAt>{{}}</LastModifiedAt>
    <Basepaths>/</Basepaths>
    <ConfigurationVersion majorVersion="4" minorVersion="0"/>
    <Policies/>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <Resources/>
    <TargetServers/>
    <TargetEndpoints>
        <TargetEndpoint>default</TargetEndpoint>
    </TargetEndpoints>
</APIProxy>'''


def generate_proxy_endpoint_xml(proxy_name, base_path):
    """Generate the apiproxy/proxies/default.xml file"""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
    <Description>Default Proxy Endpoint</Description>
    <FaultRules/>
    <PreFlow name="PreFlow">
        <Request/>
        <Response/>
    </PreFlow>
    <PostFlow name="PostFlow">
        <Request/>
        <Response/>
    </PostFlow>
    <Flows/>
    <HTTPProxyConnection>
        <BasePath>{base_path}</BasePath>
        <Properties/>
        <VirtualHost>secure</VirtualHost>
    </HTTPProxyConnection>
    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>'''


def generate_target_endpoint_xml(domain, target_path):
    """Generate the apiproxy/targets/default.xml file"""
    # Ensure domain has https:// prefix
    if not domain.startswith('http://') and not domain.startswith('https://'):
        url = f"https://{domain}"
    else:
        url = domain

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
    <Description>Default Target Endpoint</Description>
    <FaultRules/>
    <PreFlow name="PreFlow">
        <Request/>
        <Response/>
    </PreFlow>
    <PostFlow name="PostFlow">
        <Request/>
        <Response/>
    </PostFlow>
    <Flows/>
    <HTTPTargetConnection>
        <Properties/>
        <URL>{url}{target_path}</URL>
    </HTTPTargetConnection>
</TargetEndpoint>'''


def generate_apigee_bundle(proxy_name, domain, proxy_endpoint, target_endpoint):
    """Generate a complete Apigee proxy bundle as a ZIP file"""
    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Main proxy XML
        main_xml = generate_main_proxy_xml(proxy_name)
        zip_file.writestr(f"apiproxy/{proxy_name}.xml", main_xml)

        # Proxy endpoint
        proxy_xml = generate_proxy_endpoint_xml(proxy_name, proxy_endpoint)
        zip_file.writestr("apiproxy/proxies/default.xml", proxy_xml)

        # Target endpoint
        target_xml = generate_target_endpoint_xml(domain, target_endpoint)
        zip_file.writestr("apiproxy/targets/default.xml", target_xml)

        # Create placeholder directories with .gitkeep files
        zip_file.writestr("apiproxy/policies/.gitkeep", "")
        zip_file.writestr("apiproxy/resources/.gitkeep", "")

    zip_buffer.seek(0)
    return zip_buffer


def process_apigee_request(message):
    """Process an Apigee proxy generation request"""
    # Extract proxy details from message
    details, error = extract_proxy_details(message)

    if error:
        return None, None, error

    if not details:
        return None, None, "Could not understand the proxy configuration. Please specify proxy name and target domain."

    # Validate details
    valid, validation_error = validate_proxy_details(details)

    if not valid:
        # Return partial details for confirmation
        return None, details, validation_error

    # Generate the bundle
    try:
        zip_buffer = generate_apigee_bundle(
            details['proxy_name'],
            details['domain'],
            details['proxy_endpoint'],
            details['target_endpoint']
        )
        return zip_buffer, details, None
    except Exception as e:
        print(f"[Apigee] Bundle generation error: {e}")
        return None, details, f"Failed to generate bundle: {str(e)}"
