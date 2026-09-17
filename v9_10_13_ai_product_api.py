import os, json

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

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
    if value.startswith('/'):
        host = os.environ.get('PUBLIC_BASE_URL', '').rstrip('/')
        if host:
            return host + value
    host = os.environ.get('PUBLIC_BASE_URL', 'https://marquesmater-7ap1.onrender.com').rstrip('/')
    return host + '/' + value.lstrip('/')


def handle_post(body, send_json):
    if OpenAI is None:
        send_json(503, {'ok': False, 'error': 'O módulo OpenAI ainda não está instalado no servidor.'})
        return True
    if not os.environ.get('OPENAI_API_KEY'):
        send_json(503, {'ok': False, 'error': 'A IA do MarquesMater ainda não está configurada no Render (OPENAI_API_KEY).'} )
        return True

    product = body.get('product') or {}
    task = _clean(body.get('task') or 'all', 40).lower()
    allowed = {'all', 'description', 'characteristics', 'specifications', 'applications'}
    if task not in allowed:
        task = 'all'

    image = _image_url(product.get('imageUrl') or product.get('image'))
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
        'all': 'Preenche os quatro campos: descrição, características, especificações e aplicações.',
        'description': 'Concentra-te na descrição comercial profissional.',
        'characteristics': 'Concentra-te nas características objetivas do produto.',
        'specifications': 'Concentra-te nas especificações técnicas confirmáveis.',
        'applications': 'Concentra-te nas aplicações e utilizações adequadas.'
    }[task]

    instructions = (
        'És o assistente de conteúdos do backoffice MarquesMater. Escreve em português de Portugal. '
        'Analisa a imagem do produto quando fornecida e usa também os dados estruturados. '
        'A informação deve ser profissional, clara e adequada a uma loja online de materiais, ferramentas e máquinas. '
        'NUNCA inventes números, tensões, potências, capacidades, rotações, pesos, dimensões, certificações ou outras especificações técnicas. '
        'Só coloca uma especificação como confirmada quando estiver visível na imagem ou tiver sido fornecida nos dados. '
        'Quando algo técnico não puder ser confirmado, deixa esse campo vazio ou indica que deve ser confirmado. '
        'Não uses linguagem enganadora, superlativos não comprovados ou alegações de desempenho não suportadas. '
        + task_instruction
    )

    content = [
        {'type': 'input_text', 'text': 'Dados do produto:\n' + json.dumps(context, ensure_ascii=False) + '\n\nGera o conteúdo solicitado.'}
    ]
    if image:
        content.append({'type': 'input_image', 'image_url': image, 'detail': 'high'})

    schema = {
        'type': 'object',
        'properties': {
            'description': {'type': 'string'},
            'characteristics': {'type': 'string'},
            'specifications': {'type': 'string'},
            'applications': {'type': 'string'},
            'notes': {'type': 'string'}
        },
        'required': ['description', 'characteristics', 'specifications', 'applications', 'notes'],
        'additionalProperties': False
    }

    try:
        client = OpenAI()
        response = client.responses.create(
            model=MODEL,
            store=False,
            instructions=instructions,
            input=[{'role': 'user', 'content': content}],
            text={'format': {'type': 'json_schema', 'name': 'marquesmater_product_content', 'schema': schema, 'strict': True}},
        )
        raw = response.output_text or '{}'
        data = json.loads(raw)
        send_json(200, {'ok': True, 'model': MODEL, 'content': data})
        return True
    except Exception as e:
        send_json(502, {'ok': False, 'error': 'A IA não conseguiu gerar o conteúdo: ' + str(e)[:700]})
        return True
