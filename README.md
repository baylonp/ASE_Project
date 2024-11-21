
# **Advanced Software Engineering Project - A.A. 2024/2025**

## **Collaborators**
- a
- a
- a
- a

---

## **Description**
This project implements the backend for a Gacha Game system, following a microservices architecture. Each microservice is containerized using Docker and communicates via REST APIs. The backend supports features such as:
- Authentication to the system.
- Managing an in-game currency.
- Gacha rolling (providing images and item details).
- A market system with auctions for buying and selling items.

---

## **Project Structure**

```
ASE_Project/
├── gachas/                     # Microservices source code
│   ├── authentication/         # Authentication Service
│   ├── gacha_service/          # Gacha Service
│   ├── gacha_market_service/   # Market Service
│   ├── auction_service/        # Auction Service
│   ├── nginx/                  # Gateway
│   └── docker-compose.yml      # Docker Compose file 
├── docs/                       # Documentation (OpenAPI, Postman, Locust)
│   ├── postman/                # Postman collections
│   ├── locust/                 # Performance testing files
│   ├── github-actions/         # YAML workflows for GitHub Actions
│   └── openapi.json            # API docs
└── README.md                   # Project documentation
```

---

## **Requirements**
### **Required Tools**
Ensure you have the following tools installed:
- **Docker** (latest version recommended)
- **Docker Compose** (compatible with your Docker installation)
- **Newman** (to test the endpoints)
- **Locust** (to do performance testing)
- **Python** (specific version indicated in `requirements.txt`)
- **Git** (to clone the repository)

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

2. **Pull the Docker image**
   ```bash
   sudo docker pull python:3.12-slim
   ```

---

## **Building**

1. **Create, Build & Start the Docker containers (first time)**
   This command creates the containers for each microservice:
   ```bash
   sudo docker compose up
   ```

2. **Build the Docker containers**
   This command build the containers for each microservice:
   ```bash
   sudo docker compose build
   ```

---

## **Running**

1. **Start the Docker environment**
   Start the entire microservices architecture:
   ```bash
   sudo docker compose start
   ```

2. **Access the system**
   The main gateway will be accessible at:  
   `http://127.0.0.1:5000  

---

## **Stopping**

1. **Stop the Docker environment**
   Start the entire microservices architecture:
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
   newman run docs/postman/<collection>.json
   ```

### **Performance Testing with Locust**
Performance tests evaluate how the gateway handles high loads.

1. **Run Locust:**
   ```bash
   locust -f docs/locust/locustfile.py
   ```

2. **Configure the test:**
   - Open the Locust interface at .
   - Set the number of simulated users and the request rate.
   - Start the test and analyze the results.

3. **Verify rarity distribution:**
   Locust will check that the rarity distribution for Gacha rolls remains accurate, even under high request loads.

---