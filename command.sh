curl -X POST http://127.0.0.1:5000/evaluate \
  -F "process_id=Process_1" \
  -F "email=testexample.com"


curl -X POST http://127.0.0.1:5000/evaluate \
  -F "process_id=CheckAMPM" \
  -F "time=15:20"


  curl -X POST \
  http://127.0.0.1:5000/evaluate \
  -F 'name=JohnDoe' \
  -F 'age=25' \
  -F 'password=secret123' \
  -F 'role=user' \
  -F "process_id=AssignRoleProcess"

  
  curl -X POST http://127.0.0.1:5000/evaluate \
  -F "process_id=UserValidationProcess" \
  -F "name=JohnDoe" \
  -F "age=1" \
  -F "password=secret123" \
  -F "role=user"




