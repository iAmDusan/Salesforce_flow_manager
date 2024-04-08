import testreq

response = testreq.get("https://lorenzandlorenz.my.salesforce.com")
print(response.status_code)
