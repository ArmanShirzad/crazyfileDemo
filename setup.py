from setuptools import setup, find_packages

setup(
    name="crazyflie-swarm-demo",
    version="1.0.0",
    description="Crazyflie Swarm Demo Backend",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        "numpy>=1.26.0",
        "python-multipart==0.0.6",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-dotenv==1.0.0",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1"
    ],
    python_requires=">=3.11",
)
