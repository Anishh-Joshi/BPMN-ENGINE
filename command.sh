eldy@ANISHHOST BPMN Parser % curl -X POST http://127.0.0.1:5000/evaluate \
  -F "bpmn_file=@sick_logic.bpmn" \
  -F "age=25" \
  -F "has_fever=true"


curl -X POST http://127.0.0.1:5000/evaluate \
  -F "bpmn_file=@validate_email.bpmn" \
  -F "email=test@example.com"
