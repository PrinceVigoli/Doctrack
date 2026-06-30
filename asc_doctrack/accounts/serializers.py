from rest_framework import serializers
from .models import User, Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Office
        fields = ['id', 'name', 'code', 'description', 'is_active', 'is_records_office']


class UserSerializer(serializers.ModelSerializer):
    office   = OfficeSerializer(read_only=True)
    office_id = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), source='office', write_only=True, required=False)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'office', 'office_id', 'phone', 'avatar', 'is_active'
        ]
        read_only_fields = ['id']

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
