import os, json, urllib.request

MODEL = os.environ.get('OPENAI_MODEL', 'gpt-5.6-luna')


def _clean(value, limit=6000):
    return str(value or '').strip()[:limit]


def _image_url(value):
    value = _clean(value, 120000)
    if not value:
        return None
    if value.startswith('data:image/'):
        return value
    if value.startswith('http://') or value.startswith('https://'):
        return value
    host = os.environ.get('PUBLIC_BASE_URL', 'https://marquesmater-7ap1.onrender.com').rstrip('/')
    return host + '/' + value.lstrip('/')


def handle_post(body, send_json):
    if not os.environ.get('OPENAI_API_KEY'):
        send_json(503, {'ok': False, 'error': 'A IA do MarquesMater ainda não está configurada no Render (OPENAI_API_KEY).'})
        return True

    product = body.get('product') or {}
    task = _clean(body.get('task') or 'all', 40).lower()
    allowed = {'all', 'description', 'characteristics', 'specifications', 'applications', 'chat'}
    if task not in allowed:
        task = 'all'

    image = _image_url(product.get('imageUrl') or product.get('image'))
    question = _clean(body.get('question'), 4000)
    context = {
        'sku': _clean(product.get('sku'), 200),
        'ean': _clean(product.get('ean'), 200),
        'brand': _clean(product.get('brand'), 300),
        'name': _clean(product.get('name'), 500),
        'type': _clean(product.get('type'), 200),
        'commercial_category': _clean(product.get('category'), 300),
        'commercial_subcategory': _clean(product.get('subcategory'), 300),
        'commercial_family': _clean(product.get('family'), 300),
        'rida_category': _clean(product.get('ridaCategory'), 300),
        'rida_subcategory': _clean(product.get('ridaSubcategory'), 300),
        'rida_family': _clean(product.get('ridaFamily'), 300),
        'existing_description': _clean(product.get('description'), 5000),
        'existing_characteristics': _clean(product.get('characteristics'), 4000),
        'existing_specifications': _clean(product.get('specifications'), 5000),
        'existing_applications': _clean(product.get('applications'), 4000),
    }
    task_instruction = {
        'chat': 'Responde à pergunta do administrador sobre este produto de forma direta, factual e útil. Não alteres nenhum campo do produto.',
        'all': 'Preenche os quatro campos: descrição, características, especificações e aplicações.',
        'description': 'Concentra-te na descrição comercial profissional.',
        'characteristics': 'Concentra-te nas características objetivas do produto.',
        'specifications': 'Concentra-te nas especificações técnicas confirmáveis.',
        'applications': 'Concentra-te nas aplicações e utilizações adequadas.'
    }[task]
    if task == 'chat' and not question:
        send_json(400, {'ok': False, 'error': 'Escreve uma pergunta para a IA.'})
        return True
    instructions = (
        'És o assistente de conteúdos do backoffice MarquesMater. Escreve em português de Portugal. '
        'Analisa a imagem quando fornecida e usa também os dados estruturados. Profissional, claro e adequado a uma loja online. '
        'NUNCA inventes números, tensões, potências, capacidades, rotações, pesos, dimensões, certificações ou outras especificações técnicas. '
        'Só considera confirmada uma especificação quando estiver visível na imagem ou fornecida nos dados. '
        'Quando algo técnico não puder ser confirmado, deixa o campo vazio ou indica que deve ser confirmado. '
        'Não uses alegações de desempenho não suportadas. ' + task_instruction
    )
    content = [{'type': 'input_text', 'text': 'Dados do produto:\n' + json.dumps(context, ensure_ascii=False) + ('\n\nPergunta do administrador:\n' + question if task == 'chat' else '\n\nGera o conteúdo solicitado.')} ]
    if image:
        content.append({'type': 'input_image', 'image_url': image, 'detail': 'high'})
    schema = {
        'type': 'object',
        'properties': {
            'description': {'type': 'string'},
            'characteristics': {'type': 'string'},
            'specifications': {'type': 'string'},
            'applications': {'type': 'string'},
            'notes': {'type': 'string'},
            'answer': {'type': 'string'}
        },
        'required': ['description', 'characteristics', 'specifications', 'applications', 'notes', 'answer'],
        'additionalProperties': False
    }
    payload = {
        'model': MODEL,
        'store': False,
        'instructions': instructions,
        'input': [{'role': 'user', 'content': content}],
        'text': {'format': {'type': 'json_schema', 'name': 'marquesmater_product_content', 'schema': schema, 'strict': True}}
    }
    try:
        req = urllib.request.Request(
            'https://api.openai.com/v1/responses',
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode('utf-8'))
        raw = data.get('output_text') or ''
        if not raw:
            for item in data.get('output') or []:
                for part in item.get('content') or []:
                    if part.get('type') == 'output_text':
                        raw = part.get('text') or ''
                        break
                if raw:
                    break
        result = json.loads(raw or '{}')
        if task == 'chat':
            result = {'answer': _clean(result.get('answer') or result.get('notes'), 8000), 'description': '', 'characteristics': '', 'specifications': '', 'applications': '', 'notes': ''}
        send_json(200, {'ok': True, 'model': MODEL, 'content': result})
        return True
    except Exception as e:
        send_json(502, {'ok': False, 'error': 'A IA não conseguiu gerar o conteúdo: ' + str(e)[:700]})
        return True
