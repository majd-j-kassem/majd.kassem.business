rm -rf allure-results && pytest accounts/tests --alluredir=allure-results && allure serve allure-results

