"""
Gestión de Riesgos TI — ISO 27005 / NIST RMF
Views: Dashboard, Registro de Riesgos, Activos TI, Vulnerabilidades, Auditoria
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from datetime import timedelta, date
import json, csv
from uuid import UUID

from core.models import (
    Organization,
    ITAsset,
    Risk,
    RiskReview,
    Vulnerability,
    RiskCase,
    RiskEvidence,
    RiskEngineVersionLog,
)

try:
    from training.models import UnifiedModelVersion
except Exception:
    UnifiedModelVersion = None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_org(request):
    try:
        return request.user.profile.organization
    except Exception:
        return None


def _require_org(request):
    """Return (org, None) on success, or (None, JsonResponse error) if no org."""
    org = _get_org(request)
    if org is None:
        return None, JsonResponse({'success': False, 'error': 'No organization associated with this account.'}, status=403)
    return org, None


def _risk_dict(r, include_description=True):
    return {
        'id': r.id,
        'title': r.title,
        'description': r.description if include_description else r.description[:150],
        'category': r.category,
        'category_label': r.get_category_display(),
        'likelihood': r.likelihood,
        'impact': r.impact,
        'risk_score': r.risk_score,
        'risk_level': r.risk_level,
        'status': r.status,
        'status_label': r.get_status_display(),
        'treatment_type': r.treatment_type,
        'treatment_type_label': r.get_treatment_type_display() if r.treatment_type else '',
        'treatment_plan': r.treatment_plan,
        'owner': r.owner,
        'due_date': r.due_date.isoformat() if r.due_date else None,
        'is_overdue': bool(r.due_date and r.due_date < date.today() and r.status not in ('mitigated', 'closed', 'accepted')),
        'residual_likelihood': r.residual_likelihood,
        'residual_impact': r.residual_impact,
        'residual_score': r.residual_score,
        'asset_id': r.affected_asset_id,
        'asset': r.affected_asset.name if r.affected_asset else None,
        'created_at': r.created_at.strftime('%d/%m/%Y'),
        'updated_at': r.updated_at.strftime('%d/%m/%Y'),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE VIEW
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def risk_dashboard_view(request):
    organization = _get_org(request)
    return render(request, 'risk/dashboard.html', {'organization': organization})


# ─────────────────────────────────────────────────────────────────────────────
# API — STATS GENERALES
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def risk_stats(request):
    organization = _get_org(request)
    today = date.today()

    risks  = Risk.objects.filter(organization=organization)
    assets = ITAsset.objects.filter(organization=organization)
    vulns  = Vulnerability.objects.filter(organization=organization)

    active = risks.exclude(status__in=['mitigated', 'closed', 'accepted'])

    active_list = list(active.values_list('likelihood', 'impact', 'due_date', 'status'))
    critical_n = sum(1 for l, i, *_ in active_list if l * i >= 15)
    high_n     = sum(1 for l, i, *_ in active_list if 10 <= l * i < 15)
    medium_n   = sum(1 for l, i, *_ in active_list if 5  <= l * i < 10)
    low_n      = sum(1 for l, i, *_ in active_list if l * i < 5)

    overdue = sum(
        1 for l, i, due, st in active_list
        if due and due < today and st not in ('mitigated', 'closed', 'accepted')
    )

    matrix = {}
    for r in risks.exclude(status='closed').values('likelihood', 'impact'):
        key = f"{r['likelihood']},{r['impact']}"
        matrix[key] = matrix.get(key, 0) + 1

    by_cat = {}
    for cat, label in Risk.CATEGORY_CHOICES:
        c = risks.filter(category=cat).count()
        if c:
            by_cat[label] = c

    by_status = {}
    for st, label in Risk.STATUS_CHOICES:
        c = risks.filter(status=st).count()
        if c:
            by_status[st] = {'label': label, 'count': c}

    treatment = {}
    for tt, label in Risk.TREATMENT_CHOICES:
        c = active.filter(treatment_type=tt).count()
        if c:
            treatment[label] = c
    no_treatment = active.filter(treatment_type='').count()
    if no_treatment:
        treatment['Sin definir'] = no_treatment

    top_assets = []
    for a in assets.order_by('name')[:30]:
        rc = a.risks.exclude(status='closed').count()
        vc = a.vulnerabilities.filter(status__in=['open', 'in_progress']).count()
        if rc or vc:
            top_assets.append({'name': a.name, 'risks': rc, 'vulns': vc, 'criticality': a.criticality})
    top_assets = sorted(top_assets, key=lambda x: x['risks'] + x['vulns'], reverse=True)[:5]

    trend = []
    for i in range(11, -1, -1):
        d_start = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        if i == 0:
            d_end = today
        else:
            d_end = (d_start + timedelta(days=31)).replace(day=1)
        cnt = risks.filter(created_at__date__gte=d_start, created_at__date__lt=d_end).count()
        trend.append({'month': d_start.strftime('%b %Y'), 'count': cnt})

    vuln_open     = vulns.filter(status__in=['open', 'in_progress']).count()
    vuln_critical = vulns.filter(severity='critical', status='open').count()
    vuln_by_sev = {}
    for sev, label in Vulnerability.SEVERITY_CHOICES:
        c = vulns.filter(severity=sev).exclude(status__in=['resolved', 'false_positive']).count()
        if c:
            vuln_by_sev[label] = c

    stats = {
        'total_risks': risks.count(),
        'active_risks': active.count(),
        'critical_risks': critical_n,
        'high_risks': high_n,
        'medium_risks': medium_n,
        'low_risks': low_n,
        'overdue_risks': overdue,
        'mitigated_risks': risks.filter(status='mitigated').count(),
        'accepted_risks': risks.filter(status='accepted').count(),
        'total_assets': assets.count(),
        'critical_assets': assets.filter(criticality='critical').count(),
        'open_vulns': vuln_open,
        'critical_vulns': vuln_critical,
        'vuln_by_severity': vuln_by_sev,
        'risk_matrix': matrix,
        'by_category': by_cat,
        'by_status': by_status,
        'treatment_breakdown': treatment,
        'top_assets_at_risk': top_assets,
        'trend': trend,
    }
    return JsonResponse({'success': True, 'stats': stats})


# ─────────────────────────────────────────────────────────────────────────────
# API — RIESGOS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def list_risks(request):
    organization = _get_org(request)
    qs = Risk.objects.filter(organization=organization).select_related('affected_asset')

    status_filter   = request.GET.get('status')
    category_filter = request.GET.get('category')
    level_filter    = request.GET.get('level')
    search          = request.GET.get('q', '').strip()
    overdue_only    = request.GET.get('overdue') == '1'

    if status_filter:
        qs = qs.filter(status=status_filter)
    if category_filter:
        qs = qs.filter(category=category_filter)
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(owner__icontains=search))
    if overdue_only:
        qs = qs.filter(due_date__lt=date.today()).exclude(status__in=['mitigated', 'closed', 'accepted'])

    risks_data = []
    for r in qs.order_by('-likelihood', '-impact')[:200]:
        level = r.risk_level
        if level_filter and level != level_filter:
            continue
        risks_data.append(_risk_dict(r, include_description=False))

    return JsonResponse({'success': True, 'risks': risks_data})


@login_required
def risk_detail(request, risk_id):
    organization = _get_org(request)
    try:
        risk = Risk.objects.select_related('affected_asset', 'created_by').get(
            id=risk_id, organization=organization
        )
    except Risk.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)

    reviews = list(RiskReview.objects.filter(risk=risk).select_related('reviewer').order_by('-reviewed_at')[:20])
    vulns = list(Vulnerability.objects.filter(linked_risk=risk).order_by('-discovery_date')[:10])

    data = _risk_dict(risk)
    data['reviews'] = [
        {
            'id': rv.id,
            'reviewer': rv.reviewer.get_full_name() or rv.reviewer.username if rv.reviewer else 'Sistema',
            'notes': rv.notes,
            'status_before': rv.status_before,
            'status_after': rv.status_after,
            'score_before': rv.likelihood_before * rv.impact_before,
            'score_after': rv.likelihood_after * rv.impact_after,
            'date': rv.reviewed_at.strftime('%d/%m/%Y %H:%M'),
        }
        for rv in reviews
    ]
    data['linked_vulns'] = [
        {'id': v.id, 'title': v.title, 'severity': v.severity, 'status': v.status, 'cvss_score': v.cvss_score}
        for v in vulns
    ]
    return JsonResponse({'success': True, 'risk': data})


@login_required
@require_http_methods(["POST"])
def create_risk(request):
    try:
        organization = _get_org(request)
        data = json.loads(request.body)
        risk = Risk.objects.create(
            organization=organization,
            title=data['title'],
            description=data.get('description', ''),
            category=data['category'],
            likelihood=int(data['likelihood']),
            impact=int(data['impact']),
            status=data.get('status', 'open'),
            treatment_type=data.get('treatment_type', ''),
            treatment_plan=data.get('treatment_plan', ''),
            owner=data.get('owner', ''),
            due_date=data.get('due_date') or None,
            affected_asset_id=data.get('asset_id') or None,
            residual_likelihood=int(data['residual_likelihood']) if data.get('residual_likelihood') else None,
            residual_impact=int(data['residual_impact']) if data.get('residual_impact') else None,
            created_by=request.user,
        )
        return JsonResponse({'success': True, 'risk': _risk_dict(risk)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def update_risk(request, risk_id):
    try:
        organization = _get_org(request)
        risk = Risk.objects.get(id=risk_id, organization=organization)
        data = json.loads(request.body)

        changed = any(k in data for k in ('status', 'likelihood', 'impact'))
        if changed:
            RiskReview.objects.create(
                risk=risk,
                reviewer=request.user,
                notes=data.get('review_notes', 'Actualizacion manual'),
                status_before=risk.status,
                status_after=data.get('status', risk.status),
                likelihood_before=risk.likelihood,
                impact_before=risk.impact,
                likelihood_after=int(data.get('likelihood', risk.likelihood)),
                impact_after=int(data.get('impact', risk.impact)),
            )

        for field in ['title', 'description', 'category', 'status', 'treatment_type', 'treatment_plan', 'owner']:
            if field in data:
                setattr(risk, field, data[field])
        if 'likelihood'          in data: risk.likelihood          = int(data['likelihood'])
        if 'impact'              in data: risk.impact              = int(data['impact'])
        if 'due_date'            in data: risk.due_date            = data['due_date'] or None
        if 'residual_likelihood' in data: risk.residual_likelihood = int(data['residual_likelihood']) if data['residual_likelihood'] else None
        if 'residual_impact'     in data: risk.residual_impact     = int(data['residual_impact']) if data['residual_impact'] else None
        if 'asset_id'            in data: risk.affected_asset_id   = data['asset_id'] or None
        risk.save()
        return JsonResponse({'success': True, 'risk': _risk_dict(risk)})
    except Risk.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Risk not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_risk(request, risk_id):
    try:
        organization = _get_org(request)
        Risk.objects.filter(id=risk_id, organization=organization).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def export_risks_csv(request):
    organization = _get_org(request)
    risks = Risk.objects.filter(organization=organization).select_related('affected_asset').order_by('-likelihood', '-impact')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="registro_riesgos.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['ID', 'Titulo', 'Categoria', 'Probabilidad', 'Impacto', 'Puntuacion', 'Nivel',
                     'Estado', 'Tratamiento', 'Responsable', 'Activo', 'Vencimiento',
                     'P.Residual', 'I.Residual', 'Score Residual', 'Plan de tratamiento', 'Fecha creacion'])
    for r in risks:
        writer.writerow([
            r.id, r.title, r.get_category_display(), r.likelihood, r.impact, r.risk_score, r.risk_level.upper(),
            r.get_status_display(), r.get_treatment_type_display() if r.treatment_type else '',
            r.owner, r.affected_asset.name if r.affected_asset else '',
            r.due_date or '', r.residual_likelihood or '', r.residual_impact or '', r.residual_score or '',
            r.treatment_plan, r.created_at.strftime('%d/%m/%Y'),
        ])
    return response


# ─────────────────────────────────────────────────────────────────────────────
# API — ACTIVOS TI
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def list_assets(request):
    organization = _get_org(request)
    assets = ITAsset.objects.filter(organization=organization, is_active=True)
    return JsonResponse({'success': True, 'assets': [
        {
            'id': a.id,
            'name': a.name,
            'asset_type': a.asset_type,
            'asset_type_label': a.get_asset_type_display(),
            'criticality': a.criticality,
            'criticality_label': a.get_criticality_display(),
            'owner': a.owner,
            'ip_address': a.ip_address,
            'location': a.location,
            'description': a.description,
            'risk_count': a.risks.exclude(status='closed').count(),
            'critical_risk_count': sum(1 for r in a.risks.exclude(status='closed').values_list('likelihood', 'impact') if r[0]*r[1] >= 15),
            'vuln_count': a.vulnerabilities.filter(status__in=['open', 'in_progress']).count(),
            'critical_vuln_count': a.vulnerabilities.filter(severity='critical', status='open').count(),
        }
        for a in assets
    ]})


@login_required
@require_http_methods(["POST"])
def create_asset(request):
    try:
        organization = _get_org(request)
        data = json.loads(request.body)
        asset = ITAsset.objects.create(
            organization=organization,
            name=data['name'],
            asset_type=data['asset_type'],
            description=data.get('description', ''),
            owner=data.get('owner', ''),
            ip_address=data.get('ip_address', ''),
            location=data.get('location', ''),
            criticality=data.get('criticality', 'medium'),
        )
        return JsonResponse({'success': True, 'id': asset.id, 'name': asset.name})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_asset(request, asset_id):
    try:
        organization = _get_org(request)
        ITAsset.objects.filter(id=asset_id, organization=organization).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# API — VULNERABILIDADES
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def list_vulnerabilities(request):
    organization = _get_org(request)
    qs = Vulnerability.objects.filter(organization=organization).select_related('asset', 'linked_risk')

    status_filter = request.GET.get('status')
    sev_filter    = request.GET.get('severity')
    search        = request.GET.get('q', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if sev_filter:
        qs = qs.filter(severity=sev_filter)
    if search:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=search) | Q(cve_id__icontains=search))

    return JsonResponse({'success': True, 'vulnerabilities': [
        {
            'id': v.id,
            'title': v.title,
            'description': v.description[:200],
            'cve_id': v.cve_id,
            'severity': v.severity,
            'severity_label': v.get_severity_display(),
            'status': v.status,
            'status_label': v.get_status_display(),
            'cvss_score': v.cvss_score,
            'asset': v.asset.name if v.asset else None,
            'asset_id': v.asset_id,
            'linked_risk': v.linked_risk.title[:60] if v.linked_risk else None,
            'linked_risk_id': v.linked_risk_id,
            'discovery_date': v.discovery_date.isoformat() if v.discovery_date else None,
            'due_date': v.due_date.isoformat() if v.due_date else None,
            'is_overdue': bool(v.due_date and v.due_date < date.today() and v.status not in ('resolved', 'false_positive')),
            'remediation_notes': v.remediation_notes,
        }
        for v in qs[:200]
    ]})


@login_required
@require_http_methods(["POST"])
def create_vulnerability(request):
    try:
        organization = _get_org(request)
        data = json.loads(request.body)
        vuln = Vulnerability.objects.create(
            organization=organization,
            title=data['title'],
            description=data.get('description', ''),
            cve_id=data.get('cve_id', ''),
            severity=data['severity'],
            status=data.get('status', 'open'),
            cvss_score=float(data['cvss_score']) if data.get('cvss_score') else None,
            remediation_notes=data.get('remediation_notes', ''),
            discovery_date=data.get('discovery_date') or date.today(),
            due_date=data.get('due_date') or None,
            asset_id=data.get('asset_id') or None,
            linked_risk_id=data.get('risk_id') or None,
        )
        return JsonResponse({'success': True, 'id': vuln.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def update_vulnerability(request, vuln_id):
    try:
        organization = _get_org(request)
        vuln = Vulnerability.objects.get(id=vuln_id, organization=organization)
        data = json.loads(request.body)
        for field in ['title', 'description', 'cve_id', 'severity', 'status', 'remediation_notes']:
            if field in data:
                setattr(vuln, field, data[field])
        if 'status' in data and data['status'] == 'resolved' and not vuln.resolved_date:
            vuln.resolved_date = date.today()
        if 'cvss_score' in data:
            vuln.cvss_score = float(data['cvss_score']) if data['cvss_score'] else None
        if 'due_date' in data:
            vuln.due_date = data['due_date'] or None
        if 'asset_id' in data:
            vuln.asset_id = data['asset_id'] or None
        if 'risk_id' in data:
            vuln.linked_risk_id = data['risk_id'] or None
        vuln.save()
        return JsonResponse({'success': True})
    except Vulnerability.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def delete_vulnerability(request, vuln_id):
    try:
        organization = _get_org(request)
        Vulnerability.objects.filter(id=vuln_id, organization=organization).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
# SEED DEMO DATA
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def seed_demo(request):
    try:
        organization = _get_org(request)

        if Risk.objects.filter(organization=organization).count() > 0:
            return JsonResponse({'success': False, 'error': 'Ya existen datos en el registro'})

        assets_data = [
            ('Servidor de Produccion Web', 'server',   'critical', 'ops@empresa.com',   '10.0.0.10', 'CPD Principal'),
            ('Base de Datos ERP',          'database', 'critical', 'dba@empresa.com',    '10.0.0.20', 'CPD Principal'),
            ('Portal de Clientes',         'app',      'high',     'dev@empresa.com',    '',          'AWS eu-west-1'),
            ('Firewall Perimetral',        'network',  'critical', 'netsec@empresa.com', '10.0.0.1',  'CPD Principal'),
            ('Office 365 / Exchange',      'cloud',    'high',     'it@empresa.com',     '',          'Microsoft Cloud'),
            ('VPN Corporativa',            'network',  'high',     'netsec@empresa.com', '10.0.0.5',  'CPD Principal'),
            ('Estaciones Desarrollo',      'workstation','medium', 'it@empresa.com',     '',          'Oficina Madrid'),
            ('Repositorio de Codigo',      'app',      'high',     'dev@empresa.com',    '',          'GitHub Enterprise'),
        ]
        asset_objs = {}
        for name, atype, crit, owner, ip, loc in assets_data:
            a = ITAsset.objects.create(organization=organization, name=name, asset_type=atype,
                                       criticality=crit, owner=owner, ip_address=ip, location=loc)
            asset_objs[name] = a

        today = date.today()

        risks_data = [
            ('Acceso no autorizado a base de datos de clientes',
             'Explotacion de credenciales debiles o SQL injection puede exponer datos personales de clientes.',
             'data', 5, 5, 'open', 'mitigate',
             'Implementar autenticacion multifactor, revisar permisos y auditar accesos diariamente.',
             'CISO', today + timedelta(days=30), 'Base de Datos ERP', 3, 4),

            ('Ransomware en infraestructura critica',
             'Campana de phishing dirigido puede infectar sistemas y cifrar activos criticos.',
             'cybersecurity', 4, 5, 'in_treatment', 'mitigate',
             'Segmentacion de red, backups offsite, EDR avanzado, simulacros de phishing mensuales.',
             'CISO', today + timedelta(days=15), 'Servidor de Produccion Web', 2, 5),

            ('Fuga de codigo fuente propietario',
             'Desarrolladores con acceso excesivo pueden filtrar codigo fuente a competidores.',
             'data', 3, 4, 'in_treatment', 'mitigate',
             'Implementar DLP, revisar permisos de repositorios, activar alertas de exfiltracion.',
             'CTO', today + timedelta(days=45), 'Repositorio de Codigo', 2, 3),

            ('Interrupcion del portal de clientes',
             'Ataque DDoS o fallo de infraestructura cloud puede dejar el servicio inaccesible.',
             'operational', 3, 4, 'open', 'mitigate',
             'Contratar servicio anti-DDoS, implementar CDN, disenio arquitectura multi-AZ.',
             'CTO', today + timedelta(days=60), 'Portal de Clientes', None, None),

            ('Incumplimiento GDPR por fuga de datos',
             'Brecha de seguridad en sistemas de datos personales puede acarrear sanciones regulatorias.',
             'compliance', 3, 5, 'open', 'mitigate',
             'Auditoria de flujos de datos, DPO designado, politica de retencion y cifrado.',
             'Legal', today + timedelta(days=20), 'Base de Datos ERP', None, None),

            ('Compromiso de credenciales de O365',
             'Ataque de fuerza bruta o phishing puede comprometer cuentas corporativas de email.',
             'cybersecurity', 4, 3, 'in_treatment', 'mitigate',
             'MFA obligatorio, Conditional Access Policies, formacion a usuarios.',
             'IT Security', today + timedelta(days=10), 'Office 365 / Exchange', 2, 2),

            ('Proveedor tercero con acceso a sistemas internos',
             'Proveedor de mantenimiento tiene acceso VPN sin monitoreo adecuado.',
             'third_party', 3, 3, 'open', 'mitigate',
             'PAM (Privileged Access Management), grabacion de sesiones, revision trimestral.',
             'Auditoria', today - timedelta(days=5), 'VPN Corporativa', None, None),

            ('Fallo de backup en produccion',
             'Los backups del servidor de produccion no se verifican, riesgo de perdida de datos.',
             'operational', 2, 5, 'in_treatment', 'mitigate',
             'Automatizar verificacion de backups, almacenamiento en al menos 3 ubicaciones.',
             'Ops', today + timedelta(days=90), 'Servidor de Produccion Web', 1, 4),

            ('Shadow IT: herramientas cloud no autorizadas',
             'Empleados usan Dropbox y otras apps personales para compartir informacion corporativa.',
             'compliance', 4, 3, 'accepted', 'accept',
             'Riesgo aceptado tras analisis coste-beneficio. Monitoreo ligero implementado.',
             'CISO', None, None, None, None),

            ('Vulnerabilidades en dependencias de software',
             'Librerias de terceros desactualizadas en la aplicacion web presentan CVEs conocidas.',
             'cybersecurity', 4, 4, 'open', 'mitigate',
             'Implementar SCA (Software Composition Analysis) en CI/CD pipeline.',
             'Dev Lead', today + timedelta(days=14), 'Portal de Clientes', 2, 3),

            ('Perdida de laptop con datos sensibles',
             'Dispositivos de empleados sin cifrado de disco completo pueden exponer datos en caso de robo.',
             'data', 3, 3, 'mitigated', 'mitigate',
             'BitLocker activado en todos los dispositivos, politica de bloqueo automatico.',
             'IT', None, 'Estaciones Desarrollo', 1, 1),

            ('Acceso fisico no autorizado al CPD',
             'Control de acceso fisico al centro de datos sin doble factor biometrico.',
             'infrastructure', 2, 4, 'in_treatment', 'mitigate',
             'Instalar torniquetes biometricos, registros de acceso, CCTV 24/7.',
             'Facilities', today + timedelta(days=120), 'Servidor de Produccion Web', 1, 3),
        ]

        for (title, desc, cat, lik, imp, status, treat_type, plan, owner, due, asset_name, res_l, res_i) in risks_data:
            asset = asset_objs.get(asset_name) if asset_name else None
            Risk.objects.create(
                organization=organization, title=title, description=desc,
                category=cat, likelihood=lik, impact=imp, status=status,
                treatment_type=treat_type, treatment_plan=plan, owner=owner,
                due_date=due, affected_asset=asset,
                residual_likelihood=res_l, residual_impact=res_i,
                created_by=request.user,
            )

        server = asset_objs.get('Servidor de Produccion Web')
        portal = asset_objs.get('Portal de Clientes')
        db     = asset_objs.get('Base de Datos ERP')

        vulns_data = [
            ('Log4Shell RCE en servidor de aplicaciones', 'CVE-2021-44228', 'critical', 10.0, 'open', server,
             'Actualizar a Log4j 2.17.0+, aplicar workaround de JNDI lookup.'),
            ('SQL Injection en formulario de busqueda', '', 'high', 8.8, 'in_progress', portal,
             'Parametrizar todas las consultas, implementar WAF rules.'),
            ('OpenSSL Heartbleed', 'CVE-2014-0160', 'high', 7.5, 'resolved', server,
             'Actualizado a OpenSSL 1.0.1g. Certificados renovados.'),
            ('Cross-Site Scripting persistente en comentarios', '', 'medium', 6.1, 'open', portal,
             'Sanitizar input, implementar CSP header.'),
            ('MySQL sin autenticacion remota deshabilitada', '', 'critical', 9.8, 'open', db,
             'Deshabilitar acceso remoto root, revisar grants.'),
            ('Certificado SSL expirado en ambiente staging', '', 'low', 3.1, 'resolved', portal,
             'Automatizar renovacion con Lets Encrypt.'),
            ('Spring4Shell RCE', 'CVE-2022-22965', 'critical', 9.8, 'in_progress', portal,
             'Actualizar Spring Framework a 5.3.18+.'),
            ('Struts2 Remote Code Execution', 'CVE-2017-5638', 'critical', 10.0, 'open', server,
             'Actualizar Apache Struts a version parcheada, aplicar WAF virtual patch.'),
        ]

        risk_objs = list(Risk.objects.filter(organization=organization))
        for i, (title, cve, sev, cvss, status, asset, remedy) in enumerate(vulns_data):
            Vulnerability.objects.create(
                organization=organization, title=title, cve_id=cve, severity=sev,
                cvss_score=cvss, status=status, asset=asset,
                remediation_notes=remedy,
                discovery_date=today - timedelta(days=i * 12 + 3),
                due_date=today + timedelta(days=30 - i * 5) if status not in ('resolved',) else None,
                linked_risk=risk_objs[i % len(risk_objs)] if risk_objs else None,
            )

        return JsonResponse({'success': True, 'message': f'Datos demo cargados: {len(risks_data)} riesgos, {len(assets_data)} activos, {len(vulns_data)} vulnerabilidades'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# API — MOBILE RISK FUSION (MVP bancario)
# ─────────────────────────────────────────────────────────────────────────────

RULES_ENGINE_VERSION = 'rules-1.0.0'
FUSION_ENGINE_VERSION = 'fusion-1.0.0'


def _clamp(value, min_value=0.0, max_value=100.0):
    return max(min_value, min(max_value, float(value)))


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}
    return default


def _to_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _normalize_snapshot(payload):
    """Accept snake_case/camelCase payloads and return canonical snapshot."""
    get = lambda *keys, default=None: next((payload[k] for k in keys if k in payload), default)

    snapshot = {
        'wifi_known': _to_bool(get('wifi_known', 'wifiKnown', default=True), default=True),
        'vpn_active': _to_bool(get('vpn_active', 'vpnActive', default=False), default=False),
        'developer_options': _to_bool(get('developer_options', 'devOptionsEnabled', default=False), default=False),
        'unusual_hour': _to_bool(get('unusual_hour', 'unusualHour', default=False), default=False),
        'overlay_detected': _to_bool(get('overlay_detected', 'overlayDetected', default=False), default=False),
        'tls_valid': _to_bool(get('tls_valid', 'tlsValid', default=True), default=True),
        'unknown_app_foreground': _to_bool(get('unknown_app_foreground', 'unknownAppForeground', default=False), default=False),
        'new_sensitive_permission': _to_bool(get('new_sensitive_permission', 'newSensitivePermission', default=False), default=False),
        'dns_standard': _to_bool(get('dns_standard', 'dnsStandard', default=True), default=True),
        'recent_failed_logins': _to_int(get('recent_failed_logins', 'recentFailedLogins', default=0), default=0),
        'sideload_detected': _to_bool(get('sideload_detected', 'sideloadDetected', default=False), default=False),
    }
    snapshot['recent_failed_logins'] = max(0, snapshot['recent_failed_logins'])
    return snapshot


def _rules_score(snapshot):
    score = 0
    reasons = []

    if not snapshot['wifi_known']:
        score += 12
        reasons.append('Conexion en red WiFi no confiable')
    if snapshot['vpn_active']:
        score += 6
        reasons.append('Uso de VPN detectado (revisar legitimidad)')
    if snapshot['developer_options']:
        score += 18
        reasons.append('Developer options activadas')
    if snapshot['unusual_hour']:
        score += 8
        reasons.append('Actividad en horario inusual')
    if snapshot['overlay_detected']:
        score += 40
        reasons.append('Overlay detectado')
    if not snapshot['tls_valid']:
        score += 35
        reasons.append('Sesion TLS no valida')
    if snapshot['unknown_app_foreground']:
        score += 15
        reasons.append('App no reconocida en primer plano')
    if snapshot['new_sensitive_permission']:
        score += 18
        reasons.append('Solicitud nueva de permisos sensibles')
    if not snapshot['dns_standard']:
        score += 12
        reasons.append('DNS no estandar detectado')

    failed_login_penalty = min(snapshot['recent_failed_logins'] * 10, 25)
    if failed_login_penalty:
        score += failed_login_penalty
        reasons.append(f"Intentos de login fallidos recientes: {snapshot['recent_failed_logins']}")

    if snapshot['overlay_detected'] and not snapshot['tls_valid']:
        score += 20
        reasons.append('Combinacion critica: OVERLAY + TLS invalido')
    if snapshot['overlay_detected'] and snapshot['unknown_app_foreground']:
        score += 15
        reasons.append('Combinacion critica: OVERLAY + app desconocida')
    if snapshot['sideload_detected'] and snapshot['new_sensitive_permission']:
        score += 20
        reasons.append('Combinacion critica: sideload + permisos sensibles')

    return _clamp(score), reasons


def _model_projection(snapshot):
    """MVP proxy until direct mobile feature extraction to XGBoost is wired."""
    if snapshot['overlay_detected'] and not snapshot['tls_valid']:
        return 92.0, 'Bot', 0.92, 'Patron compatible con banking trojan (overlay + TLS invalido)'
    if snapshot['recent_failed_logins'] >= 3 and snapshot['unusual_hour']:
        return 80.0, 'BruteForce', 0.84, 'Patron de fuerza bruta en ventana temporal corta'
    if snapshot['new_sensitive_permission'] and snapshot['unknown_app_foreground']:
        return 78.0, 'Infiltration', 0.79, 'App potencialmente invasiva con permisos sensibles'
    if (not snapshot['dns_standard']) and (not snapshot['wifi_known']):
        return 74.0, 'Bot', 0.75, 'Actividad de red anomala asociada a posible C2'
    if snapshot['sideload_detected']:
        return 68.0, 'Infiltration', 0.70, 'Instalacion sideload con riesgo operacional'
    return 18.0, 'Benign', 0.62, 'No se observa patron de ataque critico en el snapshot actual'


def _anomaly_projection(snapshot):
    rare_flags = 0
    for key in ('overlay_detected', 'developer_options', 'unknown_app_foreground', 'sideload_detected'):
        if snapshot.get(key):
            rare_flags += 1
    if not snapshot['dns_standard']:
        rare_flags += 1
    if snapshot['recent_failed_logins'] >= 3:
        rare_flags += 1
    return _clamp(rare_flags * 16)


def _sequence_projection(snapshot):
    seq = 0
    if snapshot['recent_failed_logins'] >= 2:
        seq += 35
    if snapshot['recent_failed_logins'] >= 4:
        seq += 20
    if snapshot['new_sensitive_permission'] and snapshot['unknown_app_foreground']:
        seq += 25
    if snapshot['overlay_detected'] and snapshot['new_sensitive_permission']:
        seq += 20
    return _clamp(seq)


def _impact_score(process_name, asset_criticality):
    process_baseline = {
        'payments': 90,
        'transfers': 90,
        'beneficiary_enrollment': 85,
        'onboarding': 70,
        'mobile_access': 65,
        'support': 60,
    }
    crit_bonus = {'low': -10, 'medium': 0, 'high': 8, 'critical': 15}

    base = process_baseline.get((process_name or '').strip().lower(), 60)
    bonus = crit_bonus.get((asset_criticality or 'medium').strip().lower(), 0)
    return _clamp(base + bonus)


def _control_strength(snapshot):
    control = 0
    if snapshot['wifi_known']:
        control += 30
    if snapshot['tls_valid']:
        control += 25
    if snapshot['dns_standard']:
        control += 20
    if not snapshot['developer_options']:
        control += 15
    if snapshot['recent_failed_logins'] == 0:
        control += 10
    return _clamp(control)


def _risk_band(score):
    if score >= 85:
        return 'critical'
    if score >= 70:
        return 'very_high'
    if score >= 50:
        return 'high'
    if score >= 30:
        return 'medium'
    return 'low'


def _recommended_action(level):
    actions = {
        'critical': 'Aislar red del dispositivo, bloquear sesion y abrir incidente SOC inmediato.',
        'very_high': 'Aplicar contencion automatica parcial y escalar a analista Tier-2.',
        'high': 'Requerir verificacion reforzada del usuario y monitoreo intensivo 30 minutos.',
        'medium': 'Mantener monitoreo y solicitar chequeo de seguridad al usuario.',
        'low': 'Sin bloqueo. Registrar evento para aprendizaje continuo.',
    }
    return actions.get(level, actions['low'])


def _resolve_organization(payload):
    raw_org_id = payload.get('organization_id') or payload.get('org_id')
    if not raw_org_id:
        return None
    try:
        org_uuid = UUID(str(raw_org_id))
    except Exception:
        return None
    return Organization.objects.filter(id=org_uuid).first()


def _get_active_model_version():
    if UnifiedModelVersion is None:
        return 'model-unavailable'
    active = UnifiedModelVersion.get_active()
    return f"unified-{active.version}" if active else 'model-none-active'


def _ensure_engine_versions(model_version):
    RiskEngineVersionLog.objects.get_or_create(
        engine_type='rules', version=RULES_ENGINE_VERSION,
        defaults={'is_active': True, 'notes': 'Baseline mobile ruleset for risk fusion endpoint.'}
    )
    RiskEngineVersionLog.objects.get_or_create(
        engine_type='fusion', version=FUSION_ENGINE_VERSION,
        defaults={'is_active': True, 'notes': 'Weighted fusion of rules, model, anomaly and sequence.'}
    )
    RiskEngineVersionLog.objects.get_or_create(
        engine_type='model', version=model_version,
        defaults={'is_active': True, 'notes': 'Model version consumed by mobile risk analyzer.'}
    )


def _serialize_engine_log(item):
    return {
        'id': str(item.id),
        'engine_type': item.engine_type,
        'version': item.version,
        'is_active': item.is_active,
        'checksum': item.checksum,
        'notes': item.notes,
        'created_by': item.created_by.username if item.created_by else None,
        'created_at': item.created_at.isoformat() if item.created_at else None,
    }


@csrf_exempt
@require_http_methods(["POST"])
def mobile_analyze(request):
    """POST /api/mobile/analyze - Creates a RiskCase from mobile snapshot."""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)

    snapshot = _normalize_snapshot(payload)
    process_name = payload.get('process_name', 'mobile_access')
    asset_criticality = payload.get('asset_criticality', 'medium')
    device_id = str(payload.get('device_id') or payload.get('deviceId') or '')[:64]

    rules_score, rule_reasons = _rules_score(snapshot)
    model_score, attack_class, model_confidence, model_reason = _model_projection(snapshot)
    anomaly_score = _anomaly_projection(snapshot)
    sequence_score = _sequence_projection(snapshot)

    final_likelihood = _clamp(
        0.35 * rules_score +
        0.35 * model_score +
        0.15 * anomaly_score +
        0.15 * sequence_score
    )
    impact_score = _impact_score(process_name, asset_criticality)
    control_strength = _control_strength(snapshot)
    residual_score = _clamp((0.45 * final_likelihood + 0.55 * impact_score) * (1 - control_strength / 100))

    risk_level = _risk_band(residual_score)
    recommended_action = _recommended_action(risk_level)
    confidence = max(0.0, min(1.0, (model_confidence + (rules_score / 100.0)) / 2.0))

    category_map = {
        'Bot': 'App maliciosa / spyware',
        'BruteForce': 'Intento de acceso no autorizado',
        'Infiltration': 'APT / acceso persistente',
        'PortScan': 'Reconocimiento de red',
        'DoS': 'Consumo anormal de red',
        'DDoS': 'Red comprometida / C2 activo',
        'WebAttack': 'Phishing / inyeccion',
        'Benign': 'Sin ataque critico identificado',
    }
    category = category_map.get(attack_class, 'Riesgo operacional')

    model_version = _get_active_model_version()
    _ensure_engine_versions(model_version)

    explainability = {
        'top_rule_reasons': rule_reasons[:6],
        'model_reason': model_reason,
        'weights': {'rules': 0.35, 'model': 0.35, 'anomaly': 0.15, 'sequence': 0.15},
        'scores': {
            'rules_score': round(rules_score, 2),
            'model_score': round(model_score, 2),
            'anomaly_score': round(anomaly_score, 2),
            'sequence_score': round(sequence_score, 2),
            'likelihood_score': round(final_likelihood, 2),
            'impact_score': round(impact_score, 2),
            'control_strength_score': round(control_strength, 2),
            'residual_risk_score': round(residual_score, 2),
        },
    }

    risk_case = RiskCase.objects.create(
        organization=_resolve_organization(payload),
        source_channel='mobile',
        process_name=process_name,
        attack_pattern=attack_class,
        category=category,
        asset_criticality=(asset_criticality or 'medium').lower(),
        likelihood_score=final_likelihood,
        impact_score=impact_score,
        control_strength_score=control_strength,
        residual_risk_score=residual_score,
        confidence=confidence,
        model_score=model_score,
        rules_score=rules_score,
        anomaly_score=anomaly_score,
        sequence_score=sequence_score,
        status='open',
        recommended_action=recommended_action,
        explainability_payload=explainability,
        model_version=model_version,
        rule_version=RULES_ENGINE_VERSION,
        device_id=device_id,
        raw_snapshot=snapshot,
    )

    RiskEvidence.objects.bulk_create([
        RiskEvidence(risk_case=risk_case, evidence_type='input', payload={'payload': payload, 'snapshot': snapshot}),
        RiskEvidence(risk_case=risk_case, evidence_type='scoring', payload=explainability['scores']),
        RiskEvidence(risk_case=risk_case, evidence_type='decision', payload={
            'risk_level': risk_level,
            'recommended_action': recommended_action,
            'attack_pattern': attack_class,
            'category': category,
            'confidence': round(confidence, 4),
        }),
    ])

    return JsonResponse({
        'success': True,
        'risk_case_id': str(risk_case.id),
        'attack_class': attack_class,
        'category': category,
        'risk_level': risk_level,
        'confidence': round(confidence, 4),
        'scores': explainability['scores'],
        'recommended_action': recommended_action,
        'model_version': model_version,
        'rule_version': RULES_ENGINE_VERSION,
    })


@csrf_exempt
@require_http_methods(["GET"])
def risk_case_api(request):
    """GET /api/risk/case?id=<uuid> or list recent cases."""
    risk_case_id = request.GET.get('id')

    if risk_case_id:
        try:
            case = RiskCase.objects.get(id=risk_case_id)
        except RiskCase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'RiskCase not found'}, status=404)

        evidences = list(case.evidences.order_by('created_at').values('evidence_type', 'payload', 'created_at'))
        return JsonResponse({
            'success': True,
            'risk_case': {
                'id': str(case.id),
                'process_name': case.process_name,
                'attack_pattern': case.attack_pattern,
                'category': case.category,
                'risk_level': _risk_band(case.residual_risk_score),
                'residual_risk_score': case.residual_risk_score,
                'likelihood_score': case.likelihood_score,
                'impact_score': case.impact_score,
                'control_strength_score': case.control_strength_score,
                'confidence': case.confidence,
                'recommended_action': case.recommended_action,
                'status': case.status,
                'model_version': case.model_version,
                'rule_version': case.rule_version,
                'device_id': case.device_id,
                'created_at': case.created_at.isoformat(),
                'evidences': [
                    {
                        'evidence_type': ev['evidence_type'],
                        'payload': ev['payload'],
                        'created_at': ev['created_at'].isoformat() if ev['created_at'] else None,
                    }
                    for ev in evidences
                ],
            },
        })

    status_filter = request.GET.get('status')
    limit = min(max(_to_int(request.GET.get('limit', 25), 25), 1), 200)

    qs = RiskCase.objects.all().order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)

    cases = [
        {
            'id': str(c.id),
            'process_name': c.process_name,
            'attack_pattern': c.attack_pattern,
            'category': c.category,
            'risk_level': _risk_band(c.residual_risk_score),
            'residual_risk_score': c.residual_risk_score,
            'status': c.status,
            'confidence': c.confidence,
            'created_at': c.created_at.isoformat(),
        }
        for c in qs[:limit]
    ]
    return JsonResponse({'success': True, 'count': len(cases), 'results': cases})


@csrf_exempt
@require_http_methods(["GET"])
def risk_engine_versions_api(request):
    """GET /api/risk/engine-versions?engine_type=model|rules|fusion&active_only=1"""
    engine_type = (request.GET.get('engine_type') or '').strip().lower()
    active_only = request.GET.get('active_only') == '1'
    limit = min(max(_to_int(request.GET.get('limit', 50), 50), 1), 500)

    qs = RiskEngineVersionLog.objects.all().order_by('-created_at')
    if engine_type:
        valid_types = {choice[0] for choice in RiskEngineVersionLog.ENGINE_TYPE_CHOICES}
        if engine_type not in valid_types:
            return JsonResponse({'success': False, 'error': 'Invalid engine_type'}, status=400)
        qs = qs.filter(engine_type=engine_type)
    if active_only:
        qs = qs.filter(is_active=True)

    results = [_serialize_engine_log(item) for item in qs[:limit]]
    return JsonResponse({'success': True, 'count': len(results), 'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def risk_engine_version_register_api(request):
    """POST /api/risk/engine-versions/register - Registers a new version in the audit log."""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)

    engine_type = str(payload.get('engine_type') or '').strip().lower()
    version = str(payload.get('version') or '').strip()
    notes = str(payload.get('notes') or '').strip()
    checksum = str(payload.get('checksum') or '').strip()
    is_active = bool(payload.get('is_active', False))

    valid_types = {choice[0] for choice in RiskEngineVersionLog.ENGINE_TYPE_CHOICES}
    if engine_type not in valid_types:
        return JsonResponse({'success': False, 'error': 'engine_type must be one of rules, model, fusion'}, status=400)
    if not version:
        return JsonResponse({'success': False, 'error': 'version is required'}, status=400)

    created_by = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

    with transaction.atomic():
        if is_active:
            RiskEngineVersionLog.objects.filter(engine_type=engine_type, is_active=True).update(is_active=False)

        obj, created = RiskEngineVersionLog.objects.get_or_create(
            engine_type=engine_type,
            version=version,
            defaults={
                'is_active': is_active,
                'notes': notes,
                'checksum': checksum,
                'created_by': created_by,
            },
        )

        if not created:
            changed = False
            if notes and notes != obj.notes:
                obj.notes = notes
                changed = True
            if checksum and checksum != obj.checksum:
                obj.checksum = checksum
                changed = True
            if is_active and not obj.is_active:
                obj.is_active = True
                changed = True
            if created_by and not obj.created_by:
                obj.created_by = created_by
                changed = True
            if changed:
                obj.save()

    return JsonResponse({
        'success': True,
        'created': created,
        'engine_version': _serialize_engine_log(obj),
    })


@csrf_exempt
@require_http_methods(["POST"])
def risk_engine_version_activate_api(request):
    """POST /api/risk/engine-versions/activate - Marks one version as active by engine type."""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)

    engine_type = str(payload.get('engine_type') or '').strip().lower()
    version = str(payload.get('version') or '').strip()

    valid_types = {choice[0] for choice in RiskEngineVersionLog.ENGINE_TYPE_CHOICES}
    if engine_type not in valid_types:
        return JsonResponse({'success': False, 'error': 'engine_type must be one of rules, model, fusion'}, status=400)
    if not version:
        return JsonResponse({'success': False, 'error': 'version is required'}, status=400)

    with transaction.atomic():
        target = RiskEngineVersionLog.objects.filter(engine_type=engine_type, version=version).first()
        if target is None:
            return JsonResponse({'success': False, 'error': 'Version not found for engine_type'}, status=404)

        RiskEngineVersionLog.objects.filter(engine_type=engine_type, is_active=True).exclude(id=target.id).update(is_active=False)
        if not target.is_active:
            target.is_active = True
            target.save(update_fields=['is_active'])

    return JsonResponse({'success': True, 'engine_version': _serialize_engine_log(target)})


@login_required
@require_http_methods(["GET"])
def risk_governance_summary_api(request):
    """GET /api/risk/governance-summary - Aggregated risk governance data for executive dashboard."""
    org, error = _require_org(request)
    if error:
        return error

    now = timezone.now()
    risk_cases = RiskCase.objects.filter(organization=org)
    open_cases = risk_cases.exclude(status='closed')
    critical_cases = open_cases.filter(residual_risk_score__gte=85)
    high_cases = open_cases.filter(residual_risk_score__gte=70, residual_risk_score__lt=85)

    if critical_cases.count() >= 3:
        risk_status = 'critical'
    elif critical_cases.count() >= 1 or high_cases.count() >= 3:
        risk_status = 'high'
    elif open_cases.count() >= 3:
        risk_status = 'medium'
    else:
        risk_status = 'low'

    active_model = RiskEngineVersionLog.objects.filter(engine_type='model', is_active=True).order_by('-created_at').first()
    active_rules = RiskEngineVersionLog.objects.filter(engine_type='rules', is_active=True).order_by('-created_at').first()

    trend_labels = []
    trend_data = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).date()
        trend_labels.append(d.strftime('%d/%m'))
        trend_data.append(risk_cases.filter(created_at__date=d, residual_risk_score__gte=70).count())

    recent_cases = [
        {
            'id': str(rc.id),
            'process_name': rc.process_name,
            'category': rc.category or rc.attack_pattern or 'Riesgo operacional',
            'score': round(rc.residual_risk_score, 1),
            'status': rc.status,
            'created_at': rc.created_at.isoformat(),
        }
        for rc in open_cases.order_by('-residual_risk_score', '-created_at')[:5]
    ]

    return JsonResponse({
        'success': True,
        'risk': {
            'open_cases': open_cases.count(),
            'critical_cases': critical_cases.count(),
            'high_cases': high_cases.count(),
            'status': risk_status,
            'active_model_version': active_model.version if active_model else 'N/A',
            'active_rules_version': active_rules.version if active_rules else 'N/A',
        },
        'trend': {
            'labels': trend_labels,
            'data': trend_data,
        },
        'recent_cases': recent_cases,
    })
