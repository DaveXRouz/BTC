import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/testUtils";
import { Oracle } from "../Oracle";

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        "oracle.title": "Oracle",
        "oracle.subtitle": "Cosmic Guidance & Numerology",
        "oracle.user_profile": "User Profile",
        "oracle.current_reading": "Current Reading",
        "oracle.reading_results": "Reading Results",
        "oracle.select_profile": "Select profile",
        "oracle.no_profiles": "No profiles yet",
        "oracle.add_new_profile": "Add New Profile",
        "oracle.edit_profile": "Edit Profile",
        "oracle.select_to_begin": "Select a profile to begin readings.",
        "oracle.results_placeholder":
          "Results will appear here after a reading.",
        "oracle.details_placeholder":
          "Submit a reading to see detailed analysis.",
        "oracle.new_profile": "New Profile",
        "oracle.field_name": "Name",
        "oracle.field_name_persian": "Name (Persian)",
        "oracle.field_birthday": "Birthday",
        "oracle.field_mother_name": "Mother's Name",
        "oracle.field_mother_name_persian": "Mother's Name (Persian)",
        "oracle.field_country": "Country",
        "oracle.field_city": "City",
        "oracle.error_name_required": "Name must be at least 2 characters",
        "oracle.error_birthday_required": "Birthday is required",
        "oracle.error_mother_name_required":
          "Mother's name must be at least 2 characters",
        "oracle.delete_profile": "Delete",
        "oracle.delete_confirm": "Confirm Delete",
        "oracle.primary_user": "Primary User",
        "oracle.secondary_users": "Secondary Users",
        "oracle.add_secondary": "Add User",
        "oracle.remove_user": "Remove user",
        "oracle.max_users_error": "Maximum 5 users allowed",
        "oracle.duplicate_user_error": "This user has already been added",
        "oracle.translate": "Translate to Persian",
        "oracle.tab_summary": "Summary",
        "oracle.tab_details": "Details",
        "oracle.tab_history": "History",
        "oracle.filter_all": "All",
        "oracle.filter_reading": "Readings",
        "oracle.filter_question": "Questions",
        "oracle.filter_name": "Names",
        "oracle.history_empty": "No readings yet.",
        "oracle.history_count": `${params?.count ?? 0} readings`,
        "oracle.error_history": "Failed to load reading history.",
        "common.loading": "Loading...",
        "common.save": "Save",
        "common.cancel": "Cancel",
      };
      return map[key] ?? key;
    },
    i18n: {
      language: "en",
      changeLanguage: vi.fn(),
    },
  }),
}));

vi.mock("@/services/api", () => ({
  oracle: {
    history: vi.fn().mockReturnValue(new Promise(() => {})),
  },
  translation: { translate: vi.fn() },
}));

beforeEach(() => {
  localStorage.clear();
});

describe("Oracle Page", () => {
  it("renders the page title and all sections", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(screen.getByText(/Oracle/)).toBeInTheDocument();
    });
    expect(screen.getByText("User Profile")).toBeInTheDocument();
    expect(screen.getByText("Current Reading")).toBeInTheDocument();
    expect(screen.getByText("Reading Results")).toBeInTheDocument();
  });

  it("shows user selector with no profiles initially", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(screen.getByText("No profiles yet")).toBeInTheDocument();
    });
  });

  it("shows placeholder text when no user selected", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(
        screen.getByText("Select a profile to begin readings."),
      ).toBeInTheDocument();
    });
  });

  it("opens create form when Add New Profile clicked", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(screen.getByText(/Add New Profile/)).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText(/Add New Profile/));
    expect(screen.getByText("New Profile")).toBeInTheDocument();
  });

  it("shows tabbed results with Summary, Details, History", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(screen.getByText("Summary")).toBeInTheDocument();
    });
    expect(screen.getByText("Details")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
  });

  it("shows summary placeholder by default", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(
        screen.getByText("Results will appear here after a reading."),
      ).toBeInTheDocument();
    });
  });

  it("shows primary user label", async () => {
    renderWithProviders(<Oracle />);
    await waitFor(() => {
      expect(screen.getByText("Primary User")).toBeInTheDocument();
    });
  });
});
