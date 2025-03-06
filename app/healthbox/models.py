from django.db import models


class MedicineBox(models.Model):
    """Модель коробки для хранения лекарств."""

    name = models.CharField(max_length=255, verbose_name='Название коробки')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    location = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Местоположение'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Коробка с лекарствами'
        verbose_name_plural = 'Коробки с лекарствами'


class Medicament(models.Model):
    """Базовая модель для всех типов лекарств."""

    MEDICAMENT_TYPES = (
        ('tablet', 'Таблетка'),
        ('capsule', 'Капсула'),
        ('spray', 'Спрей'),
        ('ointment', 'Мазь'),
        ('cream', 'Крем'),
        ('bandage', 'Бинт'),
        ('other', 'Другое'),
    )

    name = models.CharField(max_length=255, verbose_name='Название лекарства')
    medicament_type = models.CharField(
        max_length=50,
        choices=MEDICAMENT_TYPES,
        default='other',
        verbose_name='Тип лекарства',
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name='Срок годности'
    )
    medicine_box = models.ForeignKey(
        MedicineBox,
        related_name='medicaments',
        on_delete=models.CASCADE,
        verbose_name='Коробка',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return f'{self.name} ({self.get_medicament_type_display()})'

    class Meta:
        verbose_name = 'Лекарство'
        verbose_name_plural = 'Лекарства'


class Tablet(Medicament):
    """Модель для таблеток."""

    dosage = models.CharField(
        max_length=50, verbose_name='Дозировка'
    )  # Например, "500 мг"
    shape = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Форма'
    )  # Например, "круглая"

    class Meta:
        verbose_name = 'Таблетка'
        verbose_name_plural = 'Таблетки'


class Spray(Medicament):
    """Модель для спреев."""

    volume = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Объем (мл)',
    )
    nozzle_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Тип распылителя',
    )

    class Meta:
        verbose_name = 'Спрей'
        verbose_name_plural = 'Спреи'


class Ointment(Medicament):
    """Модель для мазей."""

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Вес (г)',
    )
    texture = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Текстура',
    )

    class Meta:
        verbose_name = 'Мазь'
        verbose_name_plural = 'Мази'
