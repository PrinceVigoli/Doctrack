from rest_framework import serializers
from .models import User, Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Office
        fields = ['id', 'name', 'code', 'description', 'is_active', 'is_records_office']


class UserSerializer(serializers.ModelSerializer):
    office    = OfficeSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'office', 'phone', 'avatar', 'is_active'
        ]
        # SECURITY: this serializer backs MeView, which any authenticated user
        # can PATCH on themselves. role/is_active are privilege fields and
        # office determines which documents a program_chair can see (see
        # Document.objects.visible_to) — none of them may be self-editable.
        # Office/role assignment happens only via RegisterSerializer, which is
        # gated behind IsRecordsAdmin.
        read_only_fields = ['id', 'role', 'is_active']

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    office_id = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), source='office', required=False)

    class Meta:
        model  = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password', 'password2', 'role', 'office_id', 'phone']

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
