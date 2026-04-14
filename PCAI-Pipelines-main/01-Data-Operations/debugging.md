
# Debugging for Pipeline 1



## Problem 1 - Firewall is closing connection to Dockerhub

### Description of the Problem
Because of the Customers Firewall we can't pull the image for postgres from dockerhub. 

### Solution
There is a postgres image that is in the HPE internal registry that is also used for installation. 

On a worker node you can see this image with: 

```
nerdctl images --namespace k8s.io | grep postgres 
```

here you see the image this is the value that you need to apply then later in the yaml file under `image:`

create this yaml file on a worker node called `postgres.yaml`: 

```yaml
apiVersion: v1
kind: Service 
metadata:
  name: postgres 
  namespace: postgres
spec:
  ports:
  - port: 5432
    protocol: TCP
    targetPort: 5432
  selector:
    run: postgres
status:
  loadBalancer: {}
---
apiVersion: v1
kind: Pod 
metadata:
  creationTimestamp: null
  Labels:
  run: postgres
  name: postgres 
  namespace: postgres
spec:
  containers:
  - image: 10.208.145.55/ezmeral-common/gcr.io/mapr-252711/apps-common/bitnami/postgresql:16.4.0-debian-12-r7
    name: postgres ports:
    - containerPort: 5432
    resources: (} env:
    - name: POSTGRES DB
    value: postgres
    - name: POSTGRES_ USER
    value: postgres
    - name: POSTGRES PASSWORD
    value: postgres 
  dnsPolicy: ClusterFirst 
  restartPolicy: Always
status: {}
```

You might need to change the ip of the registry you can get that for example when you click on the Airflow configuration and scroll down from there you get the replacement for `10.208.145.55/ezmeral-common` and this part: `gcr.io/mapr-252711/apps-common/bitnami/postgresql:16.4.0-debian-12-r7` should be the same. 
then run this on the worker node where you created the yaml:

```
kubectl apply -f postgres.yaml
```

with the following command you then get the IP Adress for the Postgres: 

```
kubectl get svc -n postgres
```
