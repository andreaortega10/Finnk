import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, AIChatMessage
from ..schemas import AIChatRequest, AIChatResponse, AIChatMessageOut, AIStatusOut
from ..auth import get_current_user
from ..config import settings
from ..services.ai import get_ai_provider, is_gemini_configured, build_financial_context

router = APIRouter(prefix="/api/ai", tags=["Assistência com Inteligência Artificial"])

@router.get("/status", response_model=AIStatusOut)
def get_ai_status(
    current_user: User = Depends(get_current_user)
):
    """Retorna o status do provedor de IA e se está em modalidade gratuita/demonstração."""
    configured = is_gemini_configured()
    return AIStatusOut(
        provider=settings.AI_PROVIDER,
        model=settings.GEMINI_MODEL,
        is_configured=configured,
        is_demo=not configured,
        free_tier=True
    )


@router.get("/diag")
def get_ai_diagnostics(
    current_user: User = Depends(get_current_user)
):
    """Diagnóstico técnico protegido para verificação da API do Google Gemini."""
    import httpx
    raw_key = settings.GEMINI_API_KEY or ""
    clean_key = raw_key.strip()
    key_masked = f"{clean_key[:6]}...{clean_key[-4:]}" if len(clean_key) >= 10 else "(vazia ou muito curta)"

    diag = {
        "provider": settings.AI_PROVIDER,
        "model_configured": settings.GEMINI_MODEL,
        "key_present": bool(clean_key),
        "key_length": len(clean_key),
        "key_masked": key_masked,
        "has_whitespace": bool(raw_key != clean_key),
        "google_api_test": {}
    }

    if not clean_key:
        diag["google_api_test"]["error"] = "Chave GEMINI_API_KEY não configurada no ambiente."
        return diag

    # Testa consulta da lista de modelos na API do Google
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers={"x-goog-api-key": clean_key})
            diag["google_api_test"]["models_status_code"] = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                flash_models = [m for m in models if "flash" in m.lower()]
                diag["google_api_test"]["total_models"] = len(models)
                diag["google_api_test"]["flash_models"] = flash_models
            else:
                diag["google_api_test"]["error_body"] = resp.text[:400]
    except Exception as e:
        diag["google_api_test"]["exception"] = str(e)

    # Testa velocidade de geração em candidatos flash 3.x
    test_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.7-flash"]
    diag["model_benchmarks"] = {}
    for mod in test_models:
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={clean_key}"
        test_payload = {
            "contents": [{"role": "user", "parts": [{"text": "Responda apenas: 'Finnk OK'"}]}],
            "generationConfig": {"maxOutputTokens": 10, "temperature": 0.1}
        }
        import time
        t0 = time.time()
        try:
            with httpx.Client(timeout=8.0) as client:
                g_resp = client.post(gen_url, json=test_payload, headers={"x-goog-api-key": clean_key})
                elapsed_ms = int((time.time() - t0) * 1000)
                if g_resp.status_code == 200:
                    cand = g_resp.json().get("candidates", [])
                    txt = cand[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip() if cand else ""
                    diag["model_benchmarks"][mod] = {"status": 200, "elapsed_ms": elapsed_ms, "reply": txt}
                else:
                    diag["model_benchmarks"][mod] = {"status": g_resp.status_code, "elapsed_ms": elapsed_ms, "error": g_resp.text[:500]}
        except Exception as ex:
            diag["model_benchmarks"][mod] = {"error": str(ex), "elapsed_ms": int((time.time() - t0) * 1000)}

    return diag


@router.get("/history", response_model=List[AIChatMessageOut])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recupera o histórico recente de conversas do usuário autenticado."""
    messages = db.query(AIChatMessage).filter(
        AIChatMessage.user_id == current_user.id
    ).order_by(AIChatMessage.created_at.asc()).limit(40).all()
    return messages


@router.delete("/history")
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exclui permanentemente todo o histórico de conversas com a IA do usuário (LGPD / Privacidade).
    Não afeta nenhum registro de transação, conta ou cálculo financeiro.
    """
    deleted_count = db.query(AIChatMessage).filter(
        AIChatMessage.user_id == current_user.id
    ).delete(synchronize_session=False)
    db.commit()

    return {
        "message": "Histórico de conversas com a IA excluído permanentemente com sucesso.",
        "deleted_count": deleted_count
    }


@router.post("/chat", response_model=AIChatResponse)
def send_chat_message(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Processa uma pergunta do usuário sobre suas finanças.
    Garante acesso estritamente de leitura, consulta cálculos determinísticos oficiais do Finnk
    e produz uma resposta em linguagem natural sem expor dados pessoais ou PII.
    """
    user_msg = (req.message or "").strip()
    if not user_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mensagem não pode ser vazia."
        )
    if len(user_msg) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mensagem enviada excede o limite máximo permitido de 1.000 caracteres."
        )

    # 1. Constrói o contexto financeiro mínimo e determinístico do usuário
    system_prompt, period_label = build_financial_context(
        db=db,
        user=current_user,
        month=req.period_month,
        year=req.period_year
    )

    # 2. Recupera o histórico recente de turnos da conversa para contexto
    past_messages = db.query(AIChatMessage).filter(
        AIChatMessage.user_id == current_user.id
    ).order_by(AIChatMessage.created_at.desc()).limit(6).all()
    
    formatted_history = [
        {"role": m.role, "content": m.content}
        for m in reversed(past_messages)
    ]

    # 3. Obtém o provedor de IA e gera a resposta
    provider = get_ai_provider()
    reply_text, provider_name = provider.generate_reply(
        prompt=user_msg,
        system_prompt=system_prompt,
        history=formatted_history
    )

    now = datetime.datetime.utcnow()

    # 4. Salva a interação no histórico isolado do usuário
    user_record = AIChatMessage(
        user_id=current_user.id,
        role="user",
        content=user_msg,
        period_analyzed=period_label,
        created_at=now
    )
    assistant_record = AIChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=reply_text,
        period_analyzed=period_label,
        created_at=now + datetime.timedelta(milliseconds=200)
    )
    db.add_all([user_record, assistant_record])
    db.commit()

    is_demo = bool(req.is_demo or not is_gemini_configured())

    return AIChatResponse(
        reply=reply_text,
        period_analyzed=period_label,
        is_demo=is_demo,
        provider=provider_name,
        timestamp=now
    )
