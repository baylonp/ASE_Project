# **Advanced Software Engineering Project - A.A. 2024/2025**


![image](https://github.com/baylonp/ASE_Project/blob/main/screen.png)


## **Collaborators**
- Davide Di Rocco  
- Luca Cremonese
- Nicolò Zarulli
- Jacopo Cioni

---

## **Description**
This project implements the backend and frontend for a Gacha Game system, following a microservices architecture. Each microservice is containerized using Docker and communicates via REST APIs. The backend supports features such as:
- Authentication to the system.
- Managing in-game currency.
- Gacha rolling.
- A market system with auctions for buying and selling items.

---

## **Requirements**
### **Required Tools**
Ensure you have the following tools installed:
- **Docker** 
- **Docker Compose** 
- **Newman** 
- **Locust** 
- **Python** 
- **Git**

### **Python Dependencies**
This project uses specific dependencies listed in the `requirements.txt` files inside the microservices. Examples:
- Flask==2.3.2
- Requests==2.31.0
- Flask-SQLAlchemy==3.0.5
- bcrypt==4.0.1

---

## **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/baylonp/ASE_Project.git
   cd ASE_Project
   ```
2. Create a  **.env**  file in the same directory of docker-compose.yml file and copy paste this:
   ```
     SECRET_KEY=<CHOOSE A SECRET KEY>
   ```

---

## **Building and Running**

1. **Create, Build & Start the Docker containers (first time)**
   This command creates and builds the containers for each microservice:
   ```bash
   sudo docker compose up --build -d
   ```

---

## **Have fun**

2. **Access the system**
   The main gateway will be accessible at:  
   https://localhost  

---

## **Stopping**

1. **Stop the Docker environment**
   Stop the entire microservices architecture:
   ```bash
   sudo docker compose stop
   ```

---

## **Testing**

### **Functional Testing with Postman**
Functional tests simulate complete usage flows. Postman collection files are available in `docs/postman/`.

1. **Run the tests with Newman:**
   Execute the collection to verify the APIs of the microservices. Use Newman (Postman CLI) to run the tests:
   ```bash
   newman run docs/TEST/F1_Drivers_Gacha_3.postman_collection.json
   ```

### **Performance Testing with Locust**
Performance tests evaluate how the gateway handles high loads.

1. **Run Locust:**
   ```bash
   locust -f docs/locust/locust-user-flow.py
   ```

2. **Configure the test:**
   - Open the Locust interface
   - Set the number of simulated users and the request rate.
   - Start the test and analyze the results.

---
