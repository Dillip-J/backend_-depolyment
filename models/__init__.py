# # models/__init__.py
# from database import Base

# from .users import User, SavedAddress, Admin
# from .providers import ServiceProvider, DoctorService, Medicine, PharmacyInventory, LabTest, LabTestOffering
# from .bookings import Booking, MedicalRecord, Review, Complaint, ServiceReport
from database import Base

from .users import User, SavedAddress, Admin
# 🚨 THE FIX: Renamed to LabOffering to prevent ImportError
from .providers import ServiceProvider, DoctorService, ProviderAvailability, Medicine, PharmacyInventory, LabTest, LabOffering
from .bookings import Booking, MedicalRecord, Review, Complaint

# 🚨 THE FIX: Exposed your new catalog items to the rest of the app!
from .catalog import Service, CatalogItem