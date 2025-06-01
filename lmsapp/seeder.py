from django.contrib.auth.hashers import make_password
from lmsapp.models import User, Role

def seed_data():
    # Check if 'superadmin' role exists, create if it doesn't
    if not Role.objects.filter(name='superadmin').exists():
        superadmin_role = Role(name='superadmin')
        superadmin_role.save()
        print("Superadmin role created.")
    else:
        superadmin_role = Role.objects.get(name='superadmin')

    # Check if a superuser already exists
    if not User.objects.filter(is_superuser=True).exists():
        # Create the superuser
        User.objects.create(
            username='superadmin',  # Replace with your desired username
            password=make_password('1234'),  # Replace with your desired password
            email='asadbek.backend@gmail.com',  # Replace with your desired email
            first_name='Asadbek',  # Replace with your desired first name
            last_name='Azamatov',  # Replace with your desired last name
            is_staff=True,
            is_active=True,
            is_superuser=True,
            role=superadmin_role  # Assign the superadmin role
        )
        print('Superuser created successfully.')
    else:
        print('Superuser already exists.')


if __name__ == '__main__':
    seed_data()