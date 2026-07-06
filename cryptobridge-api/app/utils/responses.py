from flask import jsonify

def success(data=None, message=None, status_code=200):
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

def error(message, code=None, status_code=400, details=None):
    response = {'success': False, 'error': message}
    if code:
        response['code'] = code
    if details:
        response['details'] = details
    return jsonify(response), status_code

def paginated(items, total, page, per_page):
    return jsonify({
        'success': True,
        'data': items,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
        }
    }), 200
