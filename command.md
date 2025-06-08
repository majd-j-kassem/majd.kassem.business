rm -rf allure-results && pytest accounts/tests --alluredir=allure-results && allure serve allure-results

# API Test 
cd API_POSTMAN
newman run 5_jun_api.json --folder "test_1"  -e 5_jun_env.json --reporters cli,htmlextra --reporter-htmlextra-export newman-report.html


