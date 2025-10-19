# 🍅 CouchTomatoServer

A modern **.NET 8**, cross-platform rewrite of the legendary **CouchPotatoServer**, built for movie automation and download management.

---

## 🚀 Quick Start

### 🧰 Prerequisites
- [✅ .NET SDK 8.0+](https://dotnet.microsoft.com/en-us/download)
- [🐳 Docker](https://www.docker.com/get-started) (optional for containerized runs)
- Git (for cloning and contributing)

---

# 🖥️ Run Locally (from source)

## 1️⃣ Clone and build
```bash
git clone https://github.com/CouchTomatoes/CouchTomatoServer.git
cd CouchTomatoServer
dotnet build
```
## 2️⃣ Run the API
```bash
dotnet run --project src/CouchTomato.API
```
➡️ The API will start on:  
http://localhost:8080

## 3️⃣ Explore Swagger UI
Open your browser and visit:\
👉 http://localhost:8080/swagger

## 🐋 Run with Docker
🐧 Linux / 🍎 macOS / 🪟 WSL 2
```
docker compose up --build
```
Then visit http://localhost:8080/swagger
To stop the container:
```
docker compose down
```
## 🪟 Windows PowerShell (Docker Desktop)
```
docker-compose up --build
```
To stop:
```
docker-compose down
```
## ⚙️ Configuration
Default configuration file:  
<mark>src/CouchTomato.API/appsettings.json</mark>

Setting	   Description  
ConnectionStrings:DefaultConnection	SQLite database path  

Kestrel:Endpoints:Http:Url	API host/port (defaults to http://0.0.0.0:8080)  

Logging	Logging levels (uses Serilog)  

## 🪵 Logs are written to:
logs/couchtomato-YYYYMMDD.log

## 🧱 Project Structure
```
CouchTomatoServer/
 ├── .github/workflows/        → CI pipeline
 ├── docker/                   → Docker + Compose setup
 ├── src/
 │   ├── CouchTomato.Core/     → Business logic & services
 │   ├── CouchTomato.Data/     → EF Core + SQLite context
 │   ├── CouchTomato.API/      → ASP.NET Core Web API entrypoint
 │   ├── CouchTomato.Worker/   → Background jobs / scheduler
 │   └── CouchTomato.UI/       → Blazor WebAssembly UI (frontend)
 ├── tests/
 │   └── CouchTomato.Tests/    → xUnit tests
 ├── LICENSE                   → GPL v3 license
 └── README.md
```
## 🧭 Features (Current & Planned)
✅ ASP.NET Core 8 Minimal API
✅ EF Core + SQLite persistence
✅ Structured logging via Serilog
✅ Cross-platform Docker support
🧩 Blazor WebAssembly UI (frontend) – in progress
🧩 Provider Integrations (SABnzbd, Torrent) – phase 2+
🧩 Search & Scheduler – phase 3+

## 🔧 Development Workflow

### Branch Model
- main → Stable, tagged releases
- develop → Active development
- feature/* → Individual feature PRs

### Start Development
```
git checkout -b develop
```
Then follow the feature plans under Phase 2 (beginning with <mark>feature/config-core</mark>).

## 📦 Build and Test (CLI)
```
dotnet build
dotnet test
```
To run the API and view logs:
```
dotnet run --project src/CouchTomato.API
tail -f logs/couchtomato-*.log
```
## 📜 License
This project is licensed under the GNU GPL v3 license.
See the LICENSE file for details.

## ❤️ Credits
Inspired by CouchPotatoServer by RuudBurger,
re-imagined in modern .NET 8 as CouchTomatoServer by the CouchTomatoes team.