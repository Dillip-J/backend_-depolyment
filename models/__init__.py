# # models/__init__.py
from database import Base

from .users import User, SavedAddress, Admin
# Renamed to LabOffering to prevent ImportError
from .providers import ServiceProvider, DoctorService, ProviderAvailability, Medicine, PharmacyInventory, LabTest, LabOffering
from .bookings import Booking, MedicalRecord, Review, Complaint, VideoMeeting

# catalog items to the rest of the app!
from .catalog import Service, CatalogItem

# from database import Base

# from .users import User, SavedAddress, Admin
# from .providers import ServiceProvider, DoctorService, Medicine, PharmacyInventory, LabTest, LabTestOffering
# from .bookings import Booking, MedicalRecord, Review, Complaint, ServiceReport