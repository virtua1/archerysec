import PySonarqube

user = 'admin'
password = 'admin'

host = "http://192.168.1.21"
port = "9000"

out = PySonarqube.SonarqubeAPI(host=host, port=port, user=user, password=password)

print(out.projects())