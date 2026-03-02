from django.db import models

class State(models.Model):
    state_id = models.IntegerField(primary_key=True)
    state_name = models.CharField(max_length=50)

    class Meta:
        db_table = "states"
        managed = False

class Lga(models.Model):
    uniqueid = models.IntegerField(primary_key=True)
    lga_id = models.IntegerField()
    lga_name = models.CharField(max_length=50)
    state_id = models.IntegerField()

    class Meta:
        db_table = "lga"
        managed = False

class Ward(models.Model):
    uniqueid = models.IntegerField(primary_key=True)
    ward_id = models.IntegerField()
    ward_name = models.CharField(max_length=50)
    lga_id = models.IntegerField()

    class Meta:
        db_table = "ward"
        managed = False

class PollingUnit(models.Model):
    uniqueid = models.IntegerField(primary_key=True)
    polling_unit_id = models.IntegerField(null=True)
    ward_id = models.IntegerField(null=True)
    lga_id = models.IntegerField(null=True)
    state_id = models.IntegerField(null=True)
    polling_unit_name = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = "polling_unit"
        managed = False

class AnnouncedPuResult(models.Model):
    result_id = models.IntegerField(primary_key=True)
    polling_unit_uniqueid = models.IntegerField()
    party_abbreviation = models.CharField(max_length=10)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50, null=True)
    date_entered = models.DateTimeField(null=True)
    user_ip_address = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = "announced_pu_results"
        managed = False

class AnnouncedLgaResult(models.Model):
    result_id = models.IntegerField(primary_key=True)
    lga_name = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=10)
    party_score = models.IntegerField()

    class Meta:
        db_table = "announced_lga_results"
        managed = False
