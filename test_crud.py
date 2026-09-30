from datetime import date, datetime
from database import engine, SessionLocal, Base
from models import Client, Agent, InsuranceProduct, ClaimStatus, InsuredProperty, InsuranceContract, InsuranceClaim

# 1. Создание всех таблиц в БД
Base.metadata.drop_all(bind=engine)    # удаляем, чтоб была некоторая деятельность
Base.metadata.create_all(bind=engine)


def run_test():
    db = SessionLocal()

    print("--- 1. Создание записей (CREATE) ---")
    # Создание статусов
    status_new = ClaimStatus(status_name="Новая")
    status_approved = ClaimStatus(status_name="Одобрено")
    db.add_all([status_new, status_approved])

    # Создание клиента и агента
    client = Client(full_name="Иванов Иван", date_of_birth=date(1990, 1, 1), passport_info="1234 567890",
                    contact_phone="+79991234567")
    agent = Agent(full_name="Петров Петр", position="Старший агент", department="Отдел продаж")

    # Создание продукта
    product = InsuranceProduct(name="Авто-Стандарт", type_of_insurance="КАСКО", basic_tariff=5.5)
    db.add_all([client, agent, product])
    db.commit()

    # Создание имущества
    property1 = InsuredProperty(property_type="Автомобиль", market_value=1500000, description="Toyota Camry")
    db.add(property1)
    db.commit()

    # Создание договора и привязка имущества (Связь N:M)
    contract = InsuranceContract(
        client_id=client.id,
        agent_id=agent.id,
        product_id=product.id,
        contract_date=date.today(),
        insurance_sum=1500000,
        special_conditions="Без франшизы"
    )
    contract.properties.append(property1)
    db.add(contract)
    db.commit()

    # Регистрация страхового случая
    claim = InsuranceClaim(
        contract_id=contract.id,
        status_id=status_new.id,
        incident_time=datetime.now(),
        description="ДТП на перекрестке",
        amount_of_damage=50000
    )
    db.add(claim)
    db.commit()
    print("Данные успешно добавлены!")

    print("\n--- 2. Чтение данных (READ) ---")
    # Чтение договоров клиента
    client_db = db.query(Client).filter(Client.passport_info == "1234 567890").first()
    print(f"Клиент: {client_db.full_name}")
    for c in client_db.contracts:
        print(f"  Договор #{c.id}, Сумма: {c.insurance_sum}, Продукт: {c.product.name}")
        for p in c.properties:
            print(f"  Застрахованное имущество: {p.description}")

    # Фильтрация страховых случаев по статусу
    claims = db.query(InsuranceClaim).join(ClaimStatus).filter(ClaimStatus.status_name == "Новая").all()
    print(f"Количество новых заявок: {len(claims)}")

    print("\n--- 3. Обновление данных (UPDATE) ---")
    # Агент меняет статус заявки
    claim_to_update = db.query(InsuranceClaim).first()
    approved_status = db.query(ClaimStatus).filter(ClaimStatus.status_name == "Одобрено").first()
    claim_to_update.status_id = approved_status.id
    db.commit()
    print(f"Статус заявки #{claim_to_update.id} изменен на: {claim_to_update.status.status_name}")

    print("\n--- 4. Удаление данных (DELETE) ---")
    db.delete(claim_to_update)
    db.commit()
    print("Тестовый страховой случай удален.")

    db.close()


if __name__ == "__main__":
    run_test()