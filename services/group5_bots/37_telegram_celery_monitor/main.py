# Controller & Entrypoint for Service #37
from domain import ServiceEntity
from services import ServiceLogic

def main():
    logic = ServiceLogic()
    return logic.process_task()

if __name__ == "__main__":
    print(main())
