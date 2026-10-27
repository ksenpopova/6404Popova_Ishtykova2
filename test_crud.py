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
    client2 = Client(full_name="Попова Ксения", date_of_birth=date(1990, 1, 1), passport_info="1356 567895",
                    contact_phone="+79995634567")
    agent2 = Agent(full_name="Петрова Мария", position="Старший агент", department="Отдел продаж")

    client3 = Client(full_name="Смирнова Анна", date_of_birth=date(1985, 5, 12), passport_info="4567 123456",
                     contact_phone="+79001112233")
    client4 = Client(full_name="Сидоров Алексей", date_of_birth=date(1992, 8, 20), passport_info="8901 234567",
                     contact_phone="+79223334455")
    # Создание продукта
    product = InsuranceProduct(name="Авто-Стандарт", type_of_insurance="КАСКО", basic_tariff=5.5)
    db.add_all([client, client2, client3, agent, product])
    db.commit()

    # Создание имущества
    property_bmw = InsuredProperty(property_type="Автомобиль", market_value=3500000, description="BMW X5")
    property_kia = InsuredProperty(property_type="Автомобиль", market_value=1500000, description="Kia Rio")
    db.add_all([property_bmw, property_kia])
    db.commit()

    contract1 = InsuranceContract(
        client_id=client.id, agent_id=agent.id, product_id=product.id,
        contract_date=date.today(), insurance_sum=1500000
    )
    contract1.properties.append(property_kia)

    contract2 = InsuranceContract(
        client_id=client2.id, agent_id=agent.id, product_id=product.id,
        contract_date=date.today(), insurance_sum=3500000
    )
    contract2.properties.append(property_bmw)

    db.add_all([contract1, contract2])
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
    contract.properties.append(property_kia)
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

    claim_dtp = InsuranceClaim(
        contract_id=contract2.id,
        status_id=status_new.id,
        incident_time=datetime.now(),
        description="ДТП на трассе",
        amount_of_damage=450000
    )
    db.add(claim_dtp)

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

    new_claims = db.query(InsuranceClaim).join(ClaimStatus).filter(ClaimStatus.status_name == "Новая").all()

    if not new_claims:
        print("Новых заявок нет.")
    else:
        for claim in new_claims:
            print(f"Случай #{claim.id}")
            print(f"  Клиент: {claim.contract.client.full_name}")
            print(f"  Описание: {claim.description}")
            print(f"  Заявленный ущерб: {claim.amount_of_damage} руб.")
            print(f"  Дата инцидента: {claim.incident_time.strftime('%Y-%m-%d %H:%M')}")
    # Фильтрация страховых случаев по статусу
    claims = db.query(InsuranceClaim).join(ClaimStatus).filter(ClaimStatus.status_name == "Новая").all()
    print(f"Количество новых заявок: {len(claims)}")

    print("\n--- 3. Обновление данных (UPDATE) ---")
    # Агент меняет статус заявки
    #claim_to_update = (db.query(InsuranceClaim).join(InsuranceContract).join(Client).join(ClaimStatus).filter(Client.full_name == "Попова Ксения",
    #        ClaimStatus.status_name == "Новая").first())

    claim_to_update = db.query(InsuranceClaim).filter(
        InsuranceClaim.contract_id == InsuranceContract.id,
        InsuranceContract.client_id == Client.id,
        InsuranceClaim.status_id == ClaimStatus.id,
        Client.full_name == "Попова Ксения",
        ClaimStatus.status_name == "Новая"
    ).first()

    status_new = db.query(ClaimStatus).filter(ClaimStatus.status_name == "Новая").first()
    client_ksenia = db.query(Client).filter(Client.full_name == "Иванов Иван").first()

    ksenia_contracts = db.query(InsuranceContract).filter(InsuranceContract.client_id == client_ksenia.id).all()
    contract_ids = [contract.id for contract in ksenia_contracts]

    claim_to_update2 = db.query(InsuranceClaim).filter(
        InsuranceClaim.status_id == status_new.id,
        InsuranceClaim.contract_id.in_(contract_ids)).first()

    approved_status = db.query(ClaimStatus).filter(ClaimStatus.status_name == "Одобрено").first()
    claim_to_update.status_id = approved_status.id
    claim_to_update2.status_id = approved_status.id
    db.commit()
    print(f"Статус заявки #{claim_to_update.id} изменен на: {claim_to_update.status.status_name}")
    print(f"Статус заявки #{claim_to_update2.id} изменен на: {claim_to_update.status.status_name}")

    print("\n--- 4. Удаление данных (DELETE) ---")
    db.delete(claim_to_update)
    db.commit()
    print("Тестовый страховой случай удален.")

    db.close()


if __name__ == "__main__":
    run_test()