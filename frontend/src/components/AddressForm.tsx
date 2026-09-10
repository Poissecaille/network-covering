import { useState } from "react";
import type { SubmitEvent } from "react";

type AddressFormProps = {
  onSubmit: (address: string) => void;
  isLoading: boolean;
};

export function AddressForm({ onSubmit, isLoading }: AddressFormProps) {
  const [address, setAddress] = useState("");

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    if (address.trim() !== "") {
      onSubmit(address.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={address}
        onChange={(event) => setAddress(event.target.value)}
        placeholder="Entrez une adresse"
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? "Recherche..." : "Rechercher"}
      </button>
    </form>
  );
}
