import json

import pytest
from django.urls import reverse
from organizations.models import Organization
from projects.models import Project, ProjectMember
from tasks.models import Task
from users.models import User


@pytest.fixture(autouse=True)
def enable_ee_assignments(settings):
    settings.EE_ASSIGNMENTS_ENABLED = True


@pytest.mark.django_db
def test_project_members_assign_add_remove(client):
    # Setup: create owner/project via helper
    from label_studio.tests.utils import make_project, create_business

    owner = User.objects.create(email='owner@example.com')
    owner.set_password('pw')
    owner.save()
    create_business(owner)
    org = Organization.create_organization(created_by=owner, title='Org1')
    owner.active_organization = org
    owner.save()

    # login
    from label_studio.tests.utils import signin

    assert signin(client, owner.email, 'pw').status_code == 302

    project = make_project({'title': 'P1', 'label_config': '<View></View>'}, owner)

    # user in same org
    u2 = User.objects.create(email='u2@example.com')
    create_business(u2)
    org.add_user(u2)

    # Add
    resp = client.post(
        f"/ee/projects/{project.id}/members/assign",
        data=json.dumps({"add": [u2.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert u2.id in data.get('added', [])
    assert ProjectMember.objects.filter(project=project, user=u2).exists()

    # Remove
    resp = client.post(
        f"/ee/projects/{project.id}/members/assign",
        data=json.dumps({"remove": [u2.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.json()
    assert u2.id in data.get('removed', [])
    assert not ProjectMember.objects.filter(project=project, user=u2).exists()


@pytest.mark.django_db
def test_project_members_enable_disable(client):
    from label_studio.tests.utils import make_project, create_business, signin

    owner = User.objects.create(email='owner2@example.com')
    owner.set_password('pw')
    owner.save()
    create_business(owner)
    org = Organization.create_organization(created_by=owner, title='Org2')
    owner.active_organization = org
    owner.save()
    assert signin(client, owner.email, 'pw').status_code == 302

    project = make_project({'title': 'P2', 'label_config': '<View></View>'}, owner)

    u2 = User.objects.create(email='u22@example.com')
    create_business(u2)
    org.add_user(u2)
    project.add_collaborator(u2)
    assert ProjectMember.objects.get(project=project, user=u2).enabled is True

    # Disable
    resp = client.post(
        f"/ee/projects/{project.id}/members/enable",
        data=json.dumps({"disable": [u2.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    assert ProjectMember.objects.get(project=project, user=u2).enabled is False

    # Enable
    resp = client.post(
        f"/ee/projects/{project.id}/members/enable",
        data=json.dumps({"enable": [u2.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    assert ProjectMember.objects.get(project=project, user=u2).enabled is True


@pytest.mark.django_db
def test_tasks_assign_bulk_and_single(client):
    from label_studio.tests.utils import make_project, create_business, signin

    owner = User.objects.create(email='owner3@example.com')
    owner.set_password('pw')
    owner.save()
    create_business(owner)
    org = Organization.create_organization(created_by=owner, title='Org3')
    owner.active_organization = org
    owner.save()
    assert signin(client, owner.email, 'pw').status_code == 302

    project = make_project({'title': 'P3', 'label_config': '<View></View>'}, owner)

    # Create tasks
    t1 = Task.objects.create(project=project, data={})
    t2 = Task.objects.create(project=project, data={})

    # Target user in org
    worker = User.objects.create(email='worker3@example.com')
    create_business(worker)
    org.add_user(worker)

    # Bulk assign
    resp = client.post(
        f"/ee/projects/{project.id}/tasks/assign",
        data=json.dumps({"user_id": worker.id, "task_ids": [t1.id, t2.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert set(data.get('locked', [])) == {t1.id, t2.id}

    # Single assign same again is idempotent-ish via lock refresh
    resp = client.post(
        f"/ee/projects/{project.id}/tasks/{t1.id}/assign",
        data=json.dumps({"user_id": worker.id}),
        content_type='application/json',
    )
    assert resp.status_code == 200
    assert t1.id in resp.json().get('locked', [])


@pytest.mark.django_db
def test_assign_user_not_in_org_negative(client):
    from label_studio.tests.utils import make_project, create_business, signin

    owner = User.objects.create(email='owner4@example.com')
    owner.set_password('pw')
    owner.save()
    create_business(owner)
    org = Organization.create_organization(created_by=owner, title='Org4')
    owner.active_organization = org
    owner.save()
    assert signin(client, owner.email, 'pw').status_code == 302

    project = make_project({'title': 'P4', 'label_config': '<View></View>'}, owner)

    # user in another org
    outsider = User.objects.create(email='outsider4@example.com')
    create_business(outsider)
    other_org = Organization.create_organization(created_by=outsider, title='Other')
    outsider.active_organization = other_org
    outsider.save()

    # Try add outsider to project members -> 400
    resp = client.post(
        f"/ee/projects/{project.id}/members/assign",
        data=json.dumps({"add": [outsider.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 400

    # Try assign tasks to outsider -> 400
    t = Task.objects.create(project=project, data={})
    resp = client.post(
        f"/ee/projects/{project.id}/tasks/assign",
        data=json.dumps({"user_id": outsider.id, "task_ids": [t.id]}),
        content_type='application/json',
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cross_org_actor_negative(client):
    # owner creates project in org1
    from label_studio.tests.utils import make_project, create_business, signin

    owner = User.objects.create(email='owner5@example.com')
    owner.set_password('pw')
    owner.save()
    create_business(owner)
    org1 = Organization.create_organization(created_by=owner, title='Org5-1')
    owner.active_organization = org1
    owner.save()

    project = make_project({'title': 'P5', 'label_config': '<View></View>'}, owner)

    # actor is another user in another org
    actor = User.objects.create(email='actor5@example.com')
    actor.set_password('pw')
    actor.save()
    create_business(actor)
    org2 = Organization.create_organization(created_by=actor, title='Org5-2')
    actor.active_organization = org2
    actor.save()

    # login as actor
    assert signin(client, actor.email, 'pw').status_code == 302

    # actor tries to operate on org1 project -> 403
    resp = client.post(
        f"/ee/projects/{project.id}/members/assign",
        data=json.dumps({"add": []}),
        content_type='application/json',
    )
    assert resp.status_code == 403

    resp = client.post(
        f"/ee/projects/{project.id}/tasks/assign",
        data=json.dumps({"user_id": actor.id, "task_ids": []}),
        content_type='application/json',
    )
    assert resp.status_code == 403
