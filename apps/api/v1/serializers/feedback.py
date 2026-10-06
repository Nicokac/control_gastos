from rest_framework import serializers


class FeedbackSerializer(serializers.Serializer):
    TIPO_CHOICES = [
        ("bug", "Bug / Falla"),
        ("mejora", "Sugerencia de mejora"),
        ("pregunta", "Pregunta"),
        ("otro", "Otro"),
    ]

    tipo = serializers.ChoiceField(choices=TIPO_CHOICES)
    mensaje = serializers.CharField(max_length=2000)
    technical_context = serializers.CharField(max_length=4000, required=False, allow_blank=True)
