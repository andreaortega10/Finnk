import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("=== TESTE END-TO-END FINNK ===")
    client = httpx.Client(timeout=10.0)
    
    # 1. Health check
    res = client.get("http://127.0.0.1:8000/")
    assert res.status_code == 200, f"Health check falhou: {res.text}"
    print("[OK] Backend online e responsivo")

    # 2. Cadastro / Login
    email = "mariana@finnk.com"
    pw = "123456"
    
    login_res = client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pw})
    if login_res.status_code != 200:
        reg_res = client.post(f"{BASE_URL}/auth/register", json={
            "name": "Mariana Silva",
            "email": email,
            "password": pw,
            "default_currency": "BRL"
        })
        assert reg_res.status_code == 200, f"Erro no registro: {reg_res.text}"
        token = reg_res.json()["access_token"]
        print("[OK] Usuario registrado com sucesso")
    else:
        token = login_res.json()["access_token"]
        print("[OK] Login realizado com sucesso")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Seed demo data
    seed_res = client.post(f"{BASE_URL}/auth/seed-demo", headers=headers)
    assert seed_res.status_code == 200, f"Erro no seed: {seed_res.text}"
    print("[OK] Dados de demonstracao populados")

    # 4. Resumo da Home
    home_res = client.get(f"{BASE_URL}/dashboard/home-summary", headers=headers)
    assert home_res.status_code == 200, f"Erro no resumo home: {home_res.text}"
    home_data = home_res.json()
    print(f"[OK] Home Summary calculado: Total Compromissos = R$ {home_data['total_commitments_amount']:.2f}, Pagos = R$ {home_data['paid_amount']:.2f}, Pendentes = R$ {home_data['pending_amount']:.2f}, Atrasados = R$ {home_data['overdue_amount']:.2f}")

    # 5. Dashboard Analítico
    dash_res = client.get(f"{BASE_URL}/dashboard/analytics", headers=headers)
    assert dash_res.status_code == 200, f"Erro no analytics: {dash_res.text}"
    dash_data = dash_res.json()
    print(f"[OK] Dashboard Analytics calculado: Saldo Atual = R$ {dash_data['current_balance']:.2f}, Saldo Projetado = R$ {dash_data['projected_balance']:.2f}")

    # 6. Compras Parceladas (RN05 / RN06)
    cards_res = client.get(f"{BASE_URL}/cards", headers=headers)
    cards = cards_res.json()
    assert len(cards) > 0, "Nenhum cartao retornado"
    card_id = cards[0]["id"]

    cats_res = client.get(f"{BASE_URL}/categories?type=DESPESA", headers=headers)
    cats = cats_res.json()
    cat_id = cats[0]["id"]

    inst_res = client.post(f"{BASE_URL}/installments", headers=headers, json={
        "title": "Passagem Aerea",
        "total_amount": 1000.00,
        "purchase_date": "2026-10-05",
        "first_due_date": "2026-10-15",
        "total_installments": 3,
        "credit_card_id": card_id,
        "category_id": cat_id
    })
    assert inst_res.status_code == 200, f"Erro no parcelamento: {inst_res.text}"
    inst_data = inst_res.json()
    parcelas = inst_data["installments"]
    assert len(parcelas) == 3
    assert parcelas[0]["amount"] == 333.33
    assert parcelas[1]["amount"] == 333.33
    assert parcelas[2]["amount"] == 333.34
    assert round(sum(p["amount"] for p in parcelas), 2) == 1000.00
    print("[OK] RN05 e RN06: Parcelamento com divisao exata e ajuste de centavos na ultima parcela validado (333.33 + 333.33 + 333.34 = 1000.00)")

    # 7. Alertas
    alerts_res = client.get(f"{BASE_URL}/alerts", headers=headers)
    assert alerts_res.status_code == 200
    print(f"[OK] Central de Alertas: {len(alerts_res.json())} notificacoes geradas automaticamente")

    # 8. Auditoria & LGPD
    audit_res = client.get(f"{BASE_URL}/user/audit-logs", headers=headers)
    assert audit_res.status_code == 200 and len(audit_res.json()) > 0
    print(f"[OK] RNF10: Trilha de auditoria ativa ({len(audit_res.json())} logs registrados)")

    lgpd_res = client.get(f"{BASE_URL}/user/export-data", headers=headers)
    assert lgpd_res.status_code == 200
    print("[OK] RNF04: Exportacao de dados para portabilidade LGPD funcionando")

    print("\nTODOS OS FLUXOS DE PONTA A PONTA VALIDADOS COM SUCESSO!")

if __name__ == "__main__":
    run_tests()
