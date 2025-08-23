import boto3

# Initialize the Bedrock client
client = boto3.client('bedrock')

# Replace with your session ID
session_id = "2de81d5e-e252-4fb6-969a-2498b7064880"

try:
    # Retrieve session details
    response = client.get_session(
        sessionId=session_id
    )
    
    # Print the session details
    print("Session Details:", response)
    
    # Optionally, retrieve invocation steps for more context
    invocations = client.list_invocations(
        sessionId=session_id
    )
    print("Invocation Details:", invocations)

except Exception as e:
    print("Error retrieving session:", str(e))
