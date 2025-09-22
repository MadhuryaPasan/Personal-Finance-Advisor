# streamlit-ai-chat-app-with-ollama



pip install google-auth
pip install google-auth-oauthlib





api testing 

first run streamlit and log in with google account.

then coppy the JWT token from expenceCat page. 

then run this on the terminal (make sure you are in root) -> uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

then open postman.

Expence categorizer agent details

```
select POST and add this link -> http://localhost:8000/predict

then below select "Body" tab and select "raw"

then insert this json code


{
    "transaction": "car service rs 1000"

}

after that select "Headers" tab

in the table

 01 for key select "Content-Type" for value select "aplication/json"
 02. for the second row, select "Authorization" as the key and for value enter the key that you copied "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InAuay5tLnAucGVyZXJhQGdtYW54545454MTc1NzQ5MzM1OX0.AZ2F9v3igccbhwVVTzOdFqyqdEJ_pbX1X-93jkPN5MI"  Like this. make sure to insert "Bearer" to the front like this "Bearer <your key>"

 then click send
``` 

here are other available api links

``` 
check health

Method -> GET
link -> http://localhost:8000/health
dont need to add Headera

_____________________________________________________________
Create goal

Method -> POST
link -> http://localhost:8000/create_goal
need to add the Header

add this to body
{
    "goal_name": "Vacation",
    "target_amount": 5000.0,
    "deadline": "2026-01-01",
    "current_savings": 1000.0
}

______________________________________________________________
Track Goal

Method -> POST
link -> http://localhost:8000/track_goal
need to add the Header

add this to body

{
    "goal": {"goal_name": "Vacation", "target_amount": 5000.0, "deadline": "2026-01-01", "current_savings": 1000.0, "remaining_amount": 4000.0, "monthly_savings_needed": 333, "weekly_savings_needed": 77},
    "recent_transactions": [
        {"type": "Expense", "category": "Transport", "amount": "rs 1000", "user_request": "car service rs 1000"},
        {"type": "Expense", "category": "Transport", "amount": "rs 10000", "user_request": "car service rs 1000"},
        {"type": "Income", "category": "Salary", "amount": "rs 2000", "user_request": "salary rs 2000"},
        {"type": "Income", "category": "Salary", "amount": "rs 20000", "user_request": "salary rs 2000"}
    ],
    "additional_savings": 500.0
}

______________________________________________________________
Set budget

Method -> POST
link -> http://localhost:8000/set_budget
need to add the Header

add this to body
{
    "category": "Transport",
    "monthly_limit": 500.0,
    "start_date": "2025-09-01"
}

______________________________________________________________
Set budget

Method -> POST
link -> http://localhost:8000/set_budget
need to add the Header

add this to body
{
    "budget": {
        "category": "Transport",
        "monthly_limit": 500.0, 
        "start_date": "2025-09-01", 
        "current_spent": 0.0},
        "recent_transactions": [
        {
            "type": "Expense", 
            "category": "Transport", 
            "amount": "rs 600", 
            "user_request": "car service rs 600"
        }
    ],
    "goal": 
    {
        "goal_name": "Vacation", 
        "target_amount": 5000.0
    }
}
______________________________________________________________
```

! important

the JWT token is update every time when you run the streamlit server.
so you need to copy the joken again from `expenceCat` page.