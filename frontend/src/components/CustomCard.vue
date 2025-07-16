<script lang="ts" setup>
defineProps({
  imgSrc: {
    type: String,
    required: true,
  },
  imgAlt: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  infos: {
    type: String,
    required: false,
  },
  hint: {
    type: String,
    required: false,
  },
})
</script>

<template>
  <div class="custom-card fr-mt-4w fr-mb-4w">
    <div class="custom-card-image">
      <img
        :src="imgSrc"
        :alt="imgAlt"
      >
    </div>
    <div class="custom-card-text">
      <h3 class="fr-card__title">
        {{ title }}
      </h3>
      <p>{{ description }}</p>
      <div class="infos">
        <p v-html="infos" />
      </div>
      <p
        class="hint m-0!"
        v-html="hint"
      />
    </div>
  </div>
</template>

<style scoped>
.infos p {
  line-height: 2.5;
}
.custom-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-default-grey);
}

.custom-card-text {
  padding: 1.5rem;
}

.custom-card-text li,
p {
  font-size: 0.875rem;
  line-height: 24px;
  text-align: left;
}

.custom-card-text p {
  margin-top: 1rem;
}

.custom-card-image {
  max-width: 100%;
  min-width: 272px;
}

.custom-card-image img {
  display: none;
  width: 100%;
  height: auto;
  object-fit: contain;
}

  :deep(.hint) {
    color: var(--blue-france-sun-113-625);
  }

  @media (min-width: 576px) {

  }

  @media (min-width: 768px) {
    .custom-card {
        display: flex;
        flex-direction: row;
        border: 1px solid var(--border-default-grey);
    }
    .custom-card-image img {
      display: block;
    }
  }

  @media (min-width: 992px) {
    .custom-card {
        display: flex;
        flex-direction: row;
        border: 1px solid var(--border-default-grey);
    }
  }

  @media (min-width: 1248px) {
    .infos p {
        line-height: 2.5;
    }
    .custom-card {
        display: flex;
        flex-direction: row;
        border: 1px solid var(--border-default-grey);
    }

    .custom-card-text li,
    p {
        font-size: 0.875rem;
        line-height: 24px;
        text-align: left;
    }

    .custom-card-text p {
        margin-top: 1rem;
    }
    .custom-card-image img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    :deep(.hint) {
        color: var(--blue-france-sun-113-625);
    }
  }
</style>
