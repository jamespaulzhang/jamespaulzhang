import os
import requests
from datetime import datetime, timedelta

def get_contributions(username, token):
    """从GitHub API获取用户贡献数据"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    query = f"""
    {{
        user(login: "{username}") {{
            contributionsCollection {{
                contributionCalendar {{
                    totalContributions
                    weeks {{
                        contributionDays {{
                            contributionCount
                            date
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")
    
    data = response.json()
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
