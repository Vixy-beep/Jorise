from django.contrib import admin
from .models import (
    Organization, 
    Subscription,
    APIKey,
    SecurityEvent,
    ThreatIntelligence,
    SIEMLog, 
    EDRAgent,
    EDRProcess,
    WAFRule,
    WAFLog, 
    SandboxAnalysis,
    UsageMetrics
)
from .user_models import UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'created_at', 'is_active')
    search_fields = ('name', 'domain')
    list_filter = ('is_active', 'created_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'plan', 'status', 'start_date', 'end_date')
    list_filter = ('plan', 'status')
    search_fields = ('organization__name',)


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('organization', 'key_name', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('organization__name', 'key_name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('email_notifications', 'slack_notifications')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('organization', 'event_type', 'severity', 'source_ip', 'timestamp')
    list_filter = ('event_type', 'severity', 'timestamp')
    search_fields = ('source_ip', 'description')


@admin.register(ThreatIntelligence)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    list_display = ('ioc_type', 'ioc_value', 'severity', 'first_seen', 'is_active')
    list_filter = ('ioc_type', 'severity', 'is_active')
    search_fields = ('ioc_value', 'description')


@admin.register(SIEMLog)
class SIEMLogAdmin(admin.ModelAdmin):
    list_display = ('organization', 'log_source', 'log_level', 'timestamp')
    list_filter = ('log_source', 'log_level', 'timestamp')
    search_fields = ('message',)


@admin.register(EDRAgent)
class EDRAgentAdmin(admin.ModelAdmin):
    list_display = ('organization', 'hostname', 'os', 'status', 'last_seen')
    list_filter = ('status', 'os')
    search_fields = ('hostname', 'ip_address')


@admin.register(EDRProcess)
class EDRProcessAdmin(admin.ModelAdmin):
    list_display = ('agent', 'process_name', 'pid', 'is_malicious', 'created_at')
    list_filter = ('is_malicious', 'created_at')
    search_fields = ('process_name', 'process_path')


@admin.register(WAFLog)
class WAFLogAdmin(admin.ModelAdmin):
    list_display = ('organization', 'source_ip', 'method', 'status_code', 'blocked', 'timestamp')
    list_filter = ('blocked', 'method', 'status_code', 'timestamp')
    search_fields = ('source_ip', 'url')


@admin.register(WAFRule)
class WAFRuleAdmin(admin.ModelAdmin):
    list_display = ('organization', 'name', 'rule_type', 'action', 'is_enabled')
    list_filter = ('rule_type', 'action', 'is_enabled')
    search_fields = ('name', 'pattern')


@admin.register(SandboxAnalysis)
class SandboxAnalysisAdmin(admin.ModelAdmin):
    list_display = ('organization', 'file_name', 'file_hash', 'threat_level', 'status', 'submitted_at')
    list_filter = ('threat_level', 'status', 'submitted_at')
    search_fields = ('file_name', 'file_hash')


@admin.register(UsageMetrics)
class UsageMetricsAdmin(admin.ModelAdmin):
    list_display = ('organization', 'metric_type', 'value', 'recorded_at')
    list_filter = ('metric_type', 'recorded_at')
    search_fields = ('organization__name',)
