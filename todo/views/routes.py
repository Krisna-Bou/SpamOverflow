from flask import Blueprint, jsonify, request
from uuid import UUID
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timezone
from urllib.parse import urlparse
import re
import uuid
import json
import subprocess
from urllib.error import HTTPError

api = Blueprint('api', __name__, url_prefix='/api/v1')
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def check_email(email, args):
    if "start" in args:
        com = datetime.strptime(args.get("start"), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=None)
        email.get("created_at").replace(tzinfo=None)
        if email.get("created_at") < com:
            return False
    if "before" in args:
        com = datetime.strptime(args.get("before"), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=None)
        email.get("created_at").replace(tzinfo=None)
        if email.get("created_at") > com:
            return False
    if "from" in args:
        if email.sender != args.get('from'):
            return False
    if "to" in args:
        if email.recipient != args.get('to'):
            return False
    if "state" in args:
        if email.status != args.get('state'):
            return False
    if "only_malicious" in args:
        if args.get('only_malicious') == "true" or args.get('only_malicious') == "True":
            return email.malicious
    return True

@api.route('/health')
def health():
    return jsonify({"status": "ok"})

@api.route('/customers/<customer_id>/emails', methods=['GET'])
def get_emails(customer_id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not found'}), 400
    args = request.args
    limit = 100
    offset = 0
    if "limit" in args:
        limit = int(args.get("limit"))
    if "offset" in args:
        offset = int(args.get("offset"))
    if "start" in args:
        try:
            com = datetime.strptime(args.get("start"), '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            return jsonify({'error': 'Incorrect date'}), 400
        if com.tzinfo is None:
            return jsonify({'error': 'Incorrect format'}), 400
    if "end" in args:
        try:
            com = datetime.strptime(args.get("end"), '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            return jsonify({'error': 'Incorrect date'}), 400
        if com.tzinfo is None:
            return jsonify({'error': 'Incorrect format'}), 400
    if "from" in args:
        if not (re.fullmatch(regex, args.get("from"))):
            return jsonify({'error': 'Incorrect format'}), 400
    if "to" in args:
        if not (re.fullmatch(regex, args.get("to"))):
            return jsonify({'error': 'Incorrect format'}), 400
    if "state" in args:
        status = args.get("state")
        if status != "pending" and status != "scanned" and status != "failed":
            return jsonify({'error': 'Incorrect format'}), 400
    if "only_malicious" in args:
        if "true" != args.get("only_malicious") and "false" != args.get("only_malicious"):
            return jsonify({'error': 'Incorrect format'}), 400
    if not 0 < limit <= 1000 or not 0 <= offset:
        return jsonify({'error': 'Incorrect format'}), 400

    emails = Todo.query.all()
    result = []
    count = 0
    count_limit = 0
    for email in emails:
        if count >= offset:
            if check_email(email, args) and email.get('cid') == customer_id:
                result.append(email.to_dict())
                count_limit += 1
            if count_limit == limit or count == emails.__len__():
                return jsonify(result), 200
        count += 1
    return jsonify(result), 200

@api.route('/customers/<customer_id>/emails/<id>', methods=['GET'])
def get_email(customer_id, id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not found'}), 400
    email = Todo.query.get(id)
    if email is None or email.get('cid') != customer_id:
        return jsonify({'error': 'Email not found'}), 404
    return jsonify(email.to_dict())

@api.route('/customers/<customer_id>/emails', methods=['POST'])
def create_email(customer_id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not found'}), 400
    contents = request.json.get('contents')
    id = str(Todo.query.all().__len__() + 1)
    body = str(contents.get('body'))
    spamhammer = str(request.json.get('metadata').get('spamhammer'))
    input_dict = {"id": id,"content": body,"metadata": spamhammer}
    result = subprocess.run(["./spamhammer", "scan", "--input", "-", "--output", "-"],cwd="todo/", input=json.dumps(input_dict), capture_output=True, text=True).stdout
    try:
        d = json.loads(result)
    except:
        return jsonify({'error': 'POSTING ERROR'}), 501
    links = re.findall(r"(http[^\s]+)", body)
    links2 = []
    domains_list = ""
    for link in links:
        links2.append(urlparse(link).netloc)
    links = list(dict.fromkeys(links2))
    for link in links:
        domains_list += link
        domains_list += (", ")
    domains_list.split(", ")
    if domains_list != "":
        domains_list =domains_list[:-2]
    contents = request.json.get('contents')
    email = Todo(
        id=id,
        cid=customer_id,
        subject=contents.get('subject'),
        body=contents.get('body'),
        sender=contents.get('from'),
        recipient=contents.get('to'),
        spamhammer=request.json.get('metadata').get('spamhammer'),
        malicious= d.get('malicious'),
        domains=(domains_list)
    )
    db.session.add(email)
    db.session.commit()
    return jsonify(email.to_dict()), 201


@api.route('/customers/<customer_id>/reports/recipients', methods=['GET'])
def get_recipients(customer_id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not valid'}), 500
    emails = Todo.query.all()
    email_addresses = {}
    for email in emails:
        if email.get("malicious") and email.get('cid') == customer_id:
            email_addresses[email.get("recipient")] = email_addresses.get(email.get("recipient"), 0) + 1
    email_result = []
    for email in email_addresses:
        temp_dict = {"id": email, "count": email_addresses.get(email)}
        email_result.append(temp_dict)
    result = {
        "generated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "total": email_result.__len__(),
        "data": email_result,
    }
    return jsonify(result), 200

@api.route('/customers/<customer_id>/reports/domains', methods=['GET'])
def get_domains(customer_id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not valid'}), 500
    emails = Todo.query.all()
    domain_addresses = {}
    for email in emails:
        if email.get("malicious") and email.get('cid') == customer_id:
            for domain in email.get("domains"):
                domain_addresses[domain] = domain_addresses.get(domain, 0) + 1
    domain_result = []
    for domain in domain_addresses:
        temp_dict = {"id": domain, "count": domain_addresses.get(domain)}
        domain_result.append(temp_dict)
    result = {
        "generated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "total": domain_result.__len__(),
        "data": domain_result,
    }
    return jsonify(result), 200

@api.route('/customers/<customer_id>/reports/actors', methods=['GET'])
def get_actors(customer_id):
    try:
        uuid.UUID(str(customer_id))
    except ValueError:
        return jsonify({'error': 'Email not valid'}), 500
    emails = Todo.query.all()
    actor_addresses = {}
    for email in emails:
        if email.get("malicious") and email.get('cid') == customer_id:
            actor_addresses[email.get("sender")] = actor_addresses.get(email.get("sender"), 0) + 1
    actor_result = []
    for actor in actor_addresses:
        temp_dict = {"id": actor, "count": actor_addresses.get(actor)}
        actor_result.append(temp_dict)
    result = {
        "generated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "total": actor_result.__len__(),
        "data": actor_result,
    }
    return jsonify(result), 200